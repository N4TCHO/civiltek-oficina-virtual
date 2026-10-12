"""Civiltek API: single-admin MVP. Configure a private persistent volume before production."""
import hmac
import io
import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from docx import Document
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("CIVILTEK_DB_PATH", str(ROOT / "data" / "civiltek.db")))
TOKEN = os.getenv("CIVILTEK_ADMIN_TOKEN", "")
LOCK = threading.RLock()
app = FastAPI(title="Civiltek API", version="0.4.0", docs_url=None, redoc_url=None, openapi_url=None)

ROLES = {
    "Director": "Coordina tareas, define prioridades y revisa entregables.",
    "Licitaciones": "Analiza antecedentes y requisitos de licitaciones chilenas.",
    "Presupuestos": "Analiza APU, cantidades, costos y supuestos.",
    "Calidad MOP": "Revisa protocolos y control de calidad de obras MOP.",
    "Documental": "Prepara borradores de cartas y registros.",
    "Comercial": "Prepara propuestas de servicios y comunicaciones.",
    "Auditor": "Identifica inconsistencias, riesgos y datos faltantes.",
}

def utcnow():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK:
        db = sqlite3.connect(DB_PATH, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()

@app.on_event("startup")
def setup():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS records(
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
            payload TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        db.execute("""CREATE INDEX IF NOT EXISTS idx_records_kind ON records(kind)""")

def authorize(authorization: str | None = Header(default=None)):
    if len(TOKEN) < 32:
        raise HTTPException(503, "Configure CIVILTEK_ADMIN_TOKEN with at least 32 characters.")
    expected = "Bearer " + TOKEN
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(401, "Unauthorized")

class RecordIn(BaseModel):
    kind: str
    title: str = Field(min_length=1, max_length=200)
    payload: dict = Field(default_factory=dict)

class TaskIn(BaseModel):
    role: str
    instructions: str = Field(min_length=3, max_length=12000)
    context: str = Field(default="", max_length=30000)

@app.get("/api/health")
def health():
    return {"ok": True, "version": "0.4.0", "configured": len(TOKEN) >= 32}

@app.get("/api/records", dependencies=[Depends(authorize)])
def list_records(kind: str | None = None):
    with connect() as db:
        rows = db.execute("SELECT * FROM records WHERE (? IS NULL OR kind = ?) ORDER BY updated_at DESC LIMIT 500", (kind, kind)).fetchall()
    return [dict(r) | {"payload": json.loads(r["payload"])} for r in rows]

@app.post("/api/records", dependencies=[Depends(authorize)])
def create_record(record: RecordIn):
    if record.kind not in ("project", "task", "letter", "apu"):
        raise HTTPException(422, "Unsupported record kind")
    item_id = str(uuid.uuid4())
    now = utcnow()
    with connect() as db:
        db.execute("INSERT INTO records VALUES(?,?,?,?,?,?)", (item_id, record.kind, record.title, json.dumps(record.payload, ensure_ascii=False), now, now))
    return {"id": item_id, "created_at": now}

@app.put("/api/records/{record_id}", dependencies=[Depends(authorize)])
def update_record(record_id: str, record: RecordIn):
    if record.kind not in ("project", "task", "letter", "apu"):
        raise HTTPException(422, "Unsupported record kind")
    with connect() as db:
        row = db.execute("SELECT kind FROM records WHERE id=?", (record_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Record not found")
        if row["kind"] != record.kind:
            raise HTTPException(409, "Cannot change record kind")
        db.execute("UPDATE records SET title=?, payload=?, updated_at=? WHERE id=?", (record.title, json.dumps(record.payload, ensure_ascii=False), utcnow(), record_id))
    return {"updated": True}

@app.delete("/api/records/{record_id}", dependencies=[Depends(authorize)])
def delete_record(record_id: str):
    with connect() as db:
        result = db.execute("DELETE FROM records WHERE id=?", (record_id,))
        if result.rowcount == 0:
            raise HTTPException(404, "Record not found")
    return {"deleted": True}

@app.post("/api/agents/run", dependencies=[Depends(authorize)])
async def run_agent(task: TaskIn):
    if task.role not in ROLES:
        raise HTTPException(422, "Unknown specialist")
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise HTTPException(503, "OPENROUTER_API_KEY is not configured")
    model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    system = ("Eres un especialista de la consultora Civiltek, Chile. " + ROLES[task.role] +
        " Responde en español chileno profesional. No inventes leyes, valores de mercado, "
        "normas MOP, documentos ni resultados de ensayos. Identifica los datos faltantes, "
        "explicita supuestos y exige revisión humana antes de presentar documentos oficiales. "
        "No ejecutes acciones externas ni afirmes que las ejecutaste.")
    payload = {"model": model, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": task.instructions + ("\n\nAntecedentes:\n" + task.context if task.context else "")}
    ], "temperature": 0.2, "max_tokens": 1800}
    # OpenRouter's free router selects an available free model. A paid model with
    # insufficient credits gets one automatic retry using that router.
    free_router = "openrouter/free"
    selected_model = model
    try:
        async with httpx.AsyncClient(timeout=75) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
                json=payload,
            )
            if response.status_code == 402 and selected_model != free_router:
                selected_model = free_router
                payload["model"] = free_router
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
                    json=payload,
                )
            if response.is_error:
                # Never return provider bodies: they can contain sensitive request data.
                status = response.status_code
                if status == 401 or status == 403:
                    detail = "OpenRouter rechazó la API Key o sus permisos (HTTP " + str(status) + ")."
                elif status == 402:
                    detail = "OpenRouter indica saldo insuficiente incluso para esta solicitud (HTTP 402)."
                elif status == 429:
                    detail = "Límite de solicitudes de OpenRouter alcanzado (HTTP 429). Intenta más tarde."
                elif status == 404:
                    detail = "Modelo de OpenRouter no disponible (HTTP 404)."
                else:
                    detail = "OpenRouter devolvió HTTP " + str(status) + "."
                raise HTTPException(502, detail)
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Empty model answer")
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as exc:
        raise HTTPException(502, "No fue posible obtener respuesta de OpenRouter. Comprueba disponibilidad del proveedor.") from exc
    return {"role": task.role, "model": selected_model, "draft": answer, "requires_human_review": True}

class LetterIn(BaseModel):
    number: str = Field(max_length=50)
    date: str = Field(max_length=30)
    recipient: str = Field(max_length=250)
    subject: str = Field(max_length=300)
    body: str = Field(max_length=20000)
    signer: str = Field(max_length=250)

@app.post("/api/letters/docx", dependencies=[Depends(authorize)])
def letter_docx(letter: LetterIn):
    doc = Document()
    doc.add_heading("CARTA N.º " + letter.number, level=1)
    doc.add_paragraph(letter.date)
    doc.add_paragraph("A: " + letter.recipient)
    doc.add_paragraph("MAT.: " + letter.subject)
    for paragraph in letter.body.split("\n"):
        doc.add_paragraph(paragraph)
    doc.add_paragraph("Atentamente,")
    doc.add_paragraph(letter.signer)
    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="civiltek-carta.docx"'})

@app.get("/")
def index():
    return FileResponse(ROOT / "index.html")

@app.get("/cartas")
def letters_page():
    return FileResponse(ROOT / "cartas.html")

@app.get("/agentes")
def agents_page():
    return FileResponse(ROOT / "agentes.html")

@app.get("/workspace")
def workspace_page():
    return FileResponse(ROOT / "workspace.html")
