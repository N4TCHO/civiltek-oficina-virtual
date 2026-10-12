"""Persistent asynchronous office jobs with atomic claiming and human approval."""
import asyncio
import json
import uuid
from datetime import datetime,timezone
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field

router=APIRouter(prefix="/api/jobs",tags=["oficina"])
class JobIn(BaseModel):
    objective:str=Field(min_length=12,max_length=8000)
    project:str=Field(default="Civiltek",max_length=200)
    context:str=Field(default="",max_length=16000)
class ReplyIn(BaseModel):
    message:str=Field(min_length=2,max_length=8000)
class DecisionIn(BaseModel):
    approved:bool
    note:str=Field(min_length=3,max_length=4000)
def now():return datetime.now(timezone.utc).isoformat()
def configure(connect,run_work):
    def save(db,job):
        db.execute("UPDATE records SET payload=?,updated_at=? WHERE id=? AND kind='office_job'",
                   (json.dumps(job,ensure_ascii=False),now(),job["id"]))
    def get(ident):
        with connect() as db:
            row=db.execute("SELECT payload FROM records WHERE id=? AND kind='office_job'",(ident,)).fetchone()
        if not row:raise HTTPException(404,"Encargo no encontrado")
        return json.loads(row["payload"])
    def log(job,stage,detail):
        job["events"].append({"time":now(),"stage":stage,"detail":detail[:800]})
    @router.post("")
    def create(data:JobIn):
        ident=str(uuid.uuid4())
        job={"id":ident,**data.model_dump(),"status":"En cola","stage":"Recepción",
             "events":[],"result_id":None,"question":None,"answer":None,"created_at":now()}
        log(job,"Recepción","Encargo recibido y registrado")
        with connect() as db:
            db.execute("INSERT INTO records VALUES(?,?,?,?,?,?)",
                       (ident,"office_job",data.objective[:200],json.dumps(job,ensure_ascii=False),now(),now()))
        return {"id":ident,"status":job["status"]}
    @router.get("")
    def list_jobs():
        with connect() as db:
            rows=db.execute("SELECT payload FROM records WHERE kind='office_job' ORDER BY created_at DESC LIMIT 100").fetchall()
        return {"items":[{k:j.get(k) for k in ("id","project","objective","status","stage","question","result_id","created_at")}
                         for r in rows for j in [json.loads(r["payload"])]]}
    @router.get("/{ident}")
    def read(ident:str):return get(ident)
    @router.post("/{ident}/reply")
    def reply(ident:str,data:ReplyIn):
        with connect() as db:
            job=get(ident)
            if job["status"]!="Necesita información":raise HTTPException(409,"El encargo no espera una respuesta")
            job["answer"]=data.message
            job["context"]=(job["context"]+"\nRespuesta del solicitante: "+data.message)[-16000:]
            job["status"]="En cola";job["question"]=None
            log(job,"Recepción","Antecedentes complementarios recibidos")
            save(db,job)
        return {"id":ident,"status":job["status"]}
    @router.post("/{ident}/decision")
    def decision(ident:str,data:DecisionIn):
        with connect() as db:
            job=get(ident)
            if job["status"]!="Revisión humana pendiente":raise HTTPException(409,"El trabajo no está pendiente de aprobación")
            job["status"]="Aprobado" if data.approved else "En cola"
            if not data.approved:
                job["context"]=(job["context"]+"\\nOBSERVACIONES PARA CORRECCIÓN: "+data.note+
                                "\\nVersión anterior: "+str(job.get("result_id")))[-16000:]
                job["stage"]="Corrección solicitada"
            log(job,"Aprobación",("Aprobado: " if data.approved else "Corrección solicitada: ")+data.note)
            save(db,job)
        return {"id":ident,"status":job["status"]}
    async def work_one():
        with connect() as db:
            row=db.execute("SELECT id,payload FROM records WHERE kind='office_job' AND json_extract(payload,'$.status')='En cola' ORDER BY created_at LIMIT 1").fetchone()
            if not row:return False
            job=json.loads(row["payload"])
            # Atomic claim across multiple Railway worker processes.
            updated=db.execute("UPDATE records SET payload=?,updated_at=? WHERE id=? AND json_extract(payload,'$.status')='En cola'",
                (json.dumps({**job,"status":"Trabajando","stage":"Director y especialistas"},ensure_ascii=False),now(),row["id"]))
            if updated.rowcount!=1:return False
        job["status"]="Trabajando";job["stage"]="Director y especialistas"
        log(job,"Director","Análisis y delegación iniciados")
        with connect() as db:save(db,job)
        try:
            result=await run_work(job["objective"],job["project"],job["context"])
            job["result_id"]=result["id"];job["status"]="Revisión humana pendiente";job["stage"]="Auditoría completada"
            log(job,"Auditoría","Borrador generado y enviado a revisión humana")
        except Exception as exc:
            job["status"]="Error";job["stage"]="Requiere intervención"
            log(job,"Error",str(exc)[:400])
        with connect() as db:save(db,job)
        return True
    async def worker():
        while True:
            try:
                did=await work_one()
                await asyncio.sleep(1 if did else 5)
            except asyncio.CancelledError:raise
            except Exception:
                await asyncio.sleep(10)
    return router,worker
