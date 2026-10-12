import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

_tmp = tempfile.mkdtemp(prefix='civiltek-smoke-')
if True:
    os.environ["CIVILTEK_DB_PATH"] = os.path.join(_tmp, "civiltek.db")
    os.environ["CIVILTEK_ADMIN_TOKEN"] = "civiltek-test-token-not-for-production-123456"
    from backend.main import app

    class SmokeTests(unittest.TestCase):
        def test_health_and_pages(self):
            with TestClient(app, base_url="https://testserver", headers={"Origin":"https://testserver"}) as client:
                response = client.get("/api/health")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["ok"])
                for route in ("/", "/panel", "/agentes", "/oficina", "/clientes", "/civiltek-ui.css", "/estados-pago", "/operaciones", "/estudio-licitaciones", "/apu"):
                    with self.subTest(route=route):
                        self.assertEqual(client.get(route).status_code, 200)

        def test_login_and_protected_records(self):
            with TestClient(app, base_url="https://testserver", headers={"Origin":"https://testserver"}) as client:
                self.assertEqual(client.get("/api/records").status_code, 401)
                self.assertEqual(client.post("/api/auth/login", json={"password": "wrong"}).status_code, 401)
                login = client.post("/api/auth/login", json={"password": os.environ["CIVILTEK_ADMIN_TOKEN"]})
                self.assertEqual(login.status_code, 200)
                self.assertTrue(login.json()["ok"])
                self.assertEqual(client.get("/api/auth/status").json()["authenticated"], True)
                self.assertEqual(client.get("/api/records").status_code, 200)

        def test_apu_pricing_and_excel(self):
            data={"code":"302-1","description":"Base granular","unit":"m3",
                "resources":[{"name":"Árido","type":"Materiales","unit":"m3",
                              "quantity":"1.2","unit_price":"10000"},
                             {"name":"Operario","type":"Mano de obra","unit":"h",
                              "quantity":"0.5","unit_price":"8000"}],
                "indirect_pct":"10","profit_pct":"10"}
            with TestClient(app,base_url="https://testserver",headers={"Origin":"https://testserver"}) as client:
                client.post("/api/auth/login",json={"password":os.environ["CIVILTEK_ADMIN_TOKEN"]})
                result=client.post("/api/apu/calcular",json=data)
                self.assertEqual(result.status_code,200,result.text)
                self.assertEqual(result.json()["direct_cost"],16000)
                self.assertEqual(result.json()["unit_price"],19360)
                excel=client.post("/api/apu/excel",json=data)
                self.assertEqual(excel.status_code,200,excel.text)
                self.assertTrue(excel.content.startswith(b"PK"))
                data["resources"][0]["quantity"]="-1"
                self.assertEqual(client.post("/api/apu/calcular",json=data).status_code,422)

        def test_tender_dossier_document_intake(self):
            from io import BytesIO
            from docx import Document
            with TestClient(app,base_url="https://testserver",headers={"Origin":"https://testserver"}) as client:
                client.post("/api/auth/login",json={"password":os.environ["CIVILTEK_ADMIN_TOKEN"]})
                created=client.post("/api/licitaciones/expedientes",json={"name":"Licitación de prueba vial"})
                self.assertEqual(created.status_code,200,created.text)
                ident=created.json()["id"]
                doc=Document();doc.add_paragraph("Bases técnicas de prueba y partida de pavimentación")
                buffer=BytesIO();doc.save(buffer)
                uploaded=client.post("/api/licitaciones/expedientes/"+ident+"/documentos",
                    files={"file":("bases.docx",buffer.getvalue(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
                self.assertEqual(uploaded.status_code,200,uploaded.text)
                self.assertGreater(uploaded.json()["characters"],10)
                matrix=client.get("/api/licitaciones/expedientes/"+ident+"/matriz")
                self.assertEqual(matrix.status_code,200)
                self.assertEqual(matrix.json()["documents"],1)
                self.assertTrue(all("evidence" in x for x in matrix.json()["checks"]))
                exported=client.get("/api/licitaciones/expedientes/"+ident+"/matriz.xlsx")
                self.assertEqual(exported.status_code,200,exported.text)
                self.assertTrue(exported.content.startswith(b"PK"))
                listed=client.get("/api/licitaciones/expedientes")
                self.assertTrue(any(x["id"]==ident for x in listed.json()))
                async def fake_provider(client,role,instruction,context):
                    if role=="Director":
                        content="ROLES: Licitaciones, Presupuestos\\nPLAN: analizar bases"
                    elif role=="Auditor":
                        content="BORRADOR REQUIERE REVISION HUMANA"
                    else:
                        content="Revisión preliminar: "+role
                    return {"role":role,"model":"mock-test","text":content}
                with patch("backend.main._ask_provider",new=fake_provider):
                    study=client.post("/api/licitaciones/expedientes/"+ident+"/ejecutar")
                self.assertEqual(study.status_code,200,study.text)
                self.assertEqual(study.json()["project"],"Licitación de prueba vial")
                self.assertEqual(len(study.json()["specialists"]),2)

        def test_operations_audit_and_approval_gates(self):
            with TestClient(app,base_url="https://testserver",headers={"Origin":"https://testserver"}) as client:
                client.post("/api/auth/login",json={"password":os.environ["CIVILTEK_ADMIN_TOKEN"]})
                templates=client.get("/api/operations/templates")
                self.assertEqual(templates.status_code,200)
                self.assertIn("quality",templates.json())
                create=client.post("/api/operations/workflows",json={
                    "title":"Control de calidad de prueba","project":"Obra de prueba",
                    "template":"quality","priority":"Alta"})
                self.assertEqual(create.status_code,200,create.text)
                wid=create.json()["id"];base="/api/operations/workflows/"+wid
                self.assertEqual(client.post(base+"/status",json={"status":"Aprobado","note":"No"}).status_code,409)
                self.assertEqual(client.post(base+"/status",json={"status":"En ejecución"}).status_code,200)
                self.assertEqual(client.post(base+"/status",json={"status":"En revisión"}).status_code,200)
                self.assertEqual(client.post(base+"/status",json={"status":"Aprobado"}).status_code,422)
                self.assertEqual(client.post(base+"/status",json={"status":"Aprobado","note":"Revisado"}).status_code,200)
                self.assertEqual(client.post(base+"/status",json={"status":"Cerrado"}).status_code,409)
                for i in range(5):
                    self.assertEqual(client.post(base+"/steps/"+str(i)).status_code,200)
                self.assertEqual(client.post(base+"/status",json={"status":"Cerrado"}).status_code,200)
                history=client.get(base+"/history")
                self.assertGreaterEqual(len(history.json()),9)
                listed=client.get("/api/operations/workflows")
                self.assertTrue(any(x["id"]==wid and x["status"]=="Cerrado" for x in listed.json()))

        def test_agent_workflow_with_mock_provider(self):
            async def mock_provider(client, role, instruction, context):
                if role == "Director":
                    content = "ROLES: Calidad MOP, Presupuestos\nPLAN: revisar antecedentes"
                elif role == "Auditor":
                    content = "BORRADOR REQUIERE REVISION HUMANA: verificar respaldo"
                else:
                    content = "Entregable de prueba para " + role
                return {"role":role,"model":"mock-test","text":content}
            with TestClient(app, base_url="https://testserver", headers={"Origin":"https://testserver"}) as client:
                client.post("/api/auth/login",json={"password":os.environ["CIVILTEK_ADMIN_TOKEN"]})
                with patch("backend.main._ask_provider",new=mock_provider):
                    response=client.post("/api/office/execute",json={
                        "objective":"Revisar documentación de control de calidad de obra",
                        "project":"Proyecto de prueba"})
                self.assertEqual(response.status_code,200,response.text)
                data=response.json()
                self.assertEqual(len(data["specialists"]),2)
                self.assertEqual(data["status"],"Revisión humana pendiente")
                doc=client.get("/api/office/"+data["id"]+"/docx")
                self.assertEqual(doc.status_code,200,doc.text)
                self.assertTrue(doc.content.startswith(b"PK"))

        def test_payment_calculation_and_export(self):
            data = {"contrato":"Contrato de prueba","numero":"1","items":[
                {"codigo":"101","descripcion":"Partida de prueba","unidad":"m3",
                 "cantidad_contrato":"100","precio_unitario":"5000",
                 "acumulado_anterior":"20","cantidad_periodo":"30"}]}
            with TestClient(app, base_url="https://testserver", headers={"Origin":"https://testserver"}) as client:
                client.post("/api/auth/login", json={"password":os.environ["CIVILTEK_ADMIN_TOKEN"]})
                result = client.post("/api/estados-pago/calcular",json=data)
                self.assertEqual(result.status_code,200,result.text)
                self.assertEqual(result.json()["totales"]["monto_periodo"],150000)
                self.assertEqual(result.json()["totales"]["saldo_monto"],250000)
                excel=client.post("/api/estados-pago/excel",json=data)
                self.assertEqual(excel.status_code,200,excel.text)
                self.assertTrue(excel.content.startswith(b"PK"))
                imported=client.post("/api/estados-pago/importar",
                    files={"file":("estado.xlsx",excel.content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
                self.assertEqual(imported.status_code,200,imported.text)
                self.assertEqual(imported.json()["items"][0]["codigo"],"101")
                saved=client.post("/api/estados-pago/guardar",json=data)
                self.assertEqual(saved.status_code,200,saved.text)
                self.assertTrue(saved.json()["saved"])
                listed=client.get("/api/estados-pago/guardados")
                self.assertEqual(listed.status_code,200,listed.text)
                self.assertTrue(any(x["id"]==saved.json()["id"] for x in listed.json()))
                data["items"][0]["cantidad_periodo"]="90"
                self.assertEqual(client.post("/api/estados-pago/calcular",json=data).status_code,422)

    if __name__ == "__main__":
        unittest.main()
