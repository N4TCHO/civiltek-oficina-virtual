import os
import tempfile
import unittest

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
                for route in ("/", "/panel", "/agentes", "/oficina", "/clientes", "/civiltek-ui.css", "/estados-pago"):
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
