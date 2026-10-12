"""Civiltek operational workflow: auditable tasks, deterministic transitions and templates."""
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/operations", tags=["operations"])
TEMPLATES = {
    "rfi": {"name":"Consulta técnica / RFI","steps":["Registrar consulta","Revisar antecedentes","Preparar respuesta","Validación técnica","Cerrar"]},
    "quality": {"name":"No conformidad / Calidad","steps":["Detectar hallazgo","Analizar causa","Definir acción correctiva","Verificar evidencia","Cerrar"]},
    "payment": {"name":"Estado de pago","steps":["Reunir mediciones","Conciliar partidas","Verificar protocolos","Revisión técnica y financiera","Cerrar"]},
    "bid": {"name":"Licitación / Oferta","steps":["Revisar bases","Evaluar admisibilidad","Preparar presupuesto","Revisar propuesta","Cerrar"]},
    "change": {"name":"Modificación de obra","steps":["Registrar cambio","Evaluar impacto técnico","Evaluar costo y plazo","Revisión contractual","Cerrar"]},
    "document": {"name":"Gestión documental","steps":["Recibir antecedentes","Clasificar","Preparar entregable","Revisión documental","Cerrar"]},
    "safety": {"name":"Prevención de riesgos","steps":["Registrar hallazgo","Evaluar riesgo","Definir controles","Validar implementación","Cerrar"]},
}
STATES = ("Pendiente","En ejecución","En revisión","Aprobado","Requiere correcciones","Cerrado")
TRANSITIONS = {
    "Pendiente":{"En ejecución"},
    "En ejecución":{"En revisión","Requiere correcciones"},
    "En revisión":{"Aprobado","Requiere correcciones"},
    "Requiere correcciones":{"En ejecución"},
    "Aprobado":{"Cerrado"},
    "Cerrado":set(),
}

class NewWorkflow(BaseModel):
    title: str = Field(min_length=4,max_length=220)
    project: str = Field(min_length=2,max_length=220)
    template: str
    responsible: str = Field(default="Por asignar",max_length=150)
    priority: str = "Media"
    due_date: str = Field(default="",max_length=10)
    description: str = Field(default="",max_length=10000)

class WorkflowUpdate(BaseModel):
    status: str
    note: str = Field(default="",max_length=3000)

def configure(connect, utcnow):
    def audit(db,workflow_id,kind,message):
        now=utcnow()
        payload={"workflow_id":workflow_id,"kind":kind,"message":message,"at":now}
        db.execute("INSERT INTO records VALUES(?,?,?,?,?,?)",
            (str(uuid.uuid4()),"workflow_event",kind,json.dumps(payload,ensure_ascii=False),now,now))

    @router.get("/templates")
    def templates():
        return TEMPLATES

    @router.get("/workflows")
    def list_workflows():
        with connect() as db:
            rows=db.execute("SELECT id,title,payload,created_at,updated_at FROM records WHERE kind='workflow' ORDER BY updated_at DESC LIMIT 300").fetchall()
        return [{"id":r["id"],"title":r["title"],"created_at":r["created_at"],"updated_at":r["updated_at"],**json.loads(r["payload"])} for r in rows]

    @router.post("/workflows")
    def create_workflow(data:NewWorkflow):
        if data.template not in TEMPLATES:
            raise HTTPException(422,"Tipo de proceso no reconocido")
        if data.priority not in ("Baja","Media","Alta","Crítica"):
            raise HTTPException(422,"Prioridad inválida")
        if data.due_date:
            try:datetime.strptime(data.due_date,"%Y-%m-%d")
            except ValueError:raise HTTPException(422,"Fecha inválida (AAAA-MM-DD)")
        item_id=str(uuid.uuid4());now=utcnow()
        payload=data.model_dump()|{"status":"Pendiente","steps":TEMPLATES[data.template]["steps"],
                                    "completed_steps":[],"reviewed_at":None}
        with connect() as db:
            db.execute("INSERT INTO records VALUES(?,?,?,?,?,?)",
                (item_id,"workflow",data.title,json.dumps(payload,ensure_ascii=False),now,now))
            audit(db,item_id,"created","Proceso registrado")
        return {"id":item_id,"status":"Pendiente"}

    @router.post("/workflows/{workflow_id}/status")
    def change_status(workflow_id:str,data:WorkflowUpdate):
        if data.status not in STATES:
            raise HTTPException(422,"Estado no reconocido")
        with connect() as db:
            row=db.execute("SELECT payload FROM records WHERE id=? AND kind='workflow'",(workflow_id,)).fetchone()
            if not row:raise HTTPException(404,"Proceso no encontrado")
            payload=json.loads(row["payload"]);old=payload["status"]
            if data.status not in TRANSITIONS[old]:
                raise HTTPException(409,f"Transición no permitida: {old} → {data.status}")
            if data.status in ("Aprobado","Requiere correcciones") and not data.note.strip():
                raise HTTPException(422,"La decisión requiere una observación")
            if data.status=="Cerrado" and len(payload["completed_steps"])!=len(payload["steps"]):
                raise HTTPException(409,"No se puede cerrar con etapas pendientes")
            payload["status"]=data.status
            if data.status=="Aprobado":payload["reviewed_at"]=utcnow()
            db.execute("UPDATE records SET payload=?,updated_at=? WHERE id=?",
                (json.dumps(payload,ensure_ascii=False),utcnow(),workflow_id))
            audit(db,workflow_id,"status",f"{old} → {data.status}. {data.note.strip()}")
        return {"id":workflow_id,"status":data.status}

    @router.post("/workflows/{workflow_id}/steps/{index}")
    def complete_step(workflow_id:str,index:int):
        with connect() as db:
            row=db.execute("SELECT payload FROM records WHERE id=? AND kind='workflow'",(workflow_id,)).fetchone()
            if not row:raise HTTPException(404,"Proceso no encontrado")
            payload=json.loads(row["payload"])
            if payload["status"] not in ("En ejecución","En revisión","Aprobado"):
                raise HTTPException(409,"Inicia la ejecución antes de completar etapas")
            if index<0 or index>=len(payload["steps"]):
                raise HTTPException(404,"Etapa no encontrada")
            if index in payload["completed_steps"]:
                return {"completed_steps":payload["completed_steps"]}
            payload["completed_steps"].append(index)
            db.execute("UPDATE records SET payload=?,updated_at=? WHERE id=?",
                (json.dumps(payload,ensure_ascii=False),utcnow(),workflow_id))
            audit(db,workflow_id,"step","Etapa completada: "+payload["steps"][index])
        return {"completed_steps":payload["completed_steps"]}

    @router.get("/workflows/{workflow_id}/history")
    def history(workflow_id:str):
        with connect() as db:
            parent=db.execute("SELECT id FROM records WHERE id=? AND kind='workflow'",(workflow_id,)).fetchone()
            if not parent:raise HTTPException(404,"Proceso no encontrado")
            rows=db.execute("SELECT payload FROM records WHERE kind='workflow_event' ORDER BY created_at ASC LIMIT 5000").fetchall()
        return [json.loads(r["payload"]) for r in rows if json.loads(r["payload"]).get("workflow_id")==workflow_id]

    return router
