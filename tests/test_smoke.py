import os
import tempfile
import unittest

from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory() as _tmp:
    os.environ["CIVILTEK_DB_PATH"] = os.path.join(_tmp, "civiltek.db")
    os.environ["CIVILTEK_ADMIN_TOKEN"] = "civiltek-test-token-not-for-production-123456"
    from backend.main import app

    class SmokeTests(unittest.TestCase):
        def test_health_and_pages(self):
            with TestClient(app, base_url="https://testserver") as client:
                response = client.get("/api/health")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["ok"])
                for route in ("/", "/panel", "/agentes", "/oficina", "/clientes"):
                    with self.subTest(route=route):
                        self.assertEqual(client.get(route).status_code, 200)

        def test_login_and_protected_records(self):
            with TestClient(app, base_url="https://testserver") as client:
                self.assertEqual(client.get("/api/records").status_code, 401)
                self.assertEqual(client.post("/api/auth/login", json={"password": "wrong"}).status_code, 401)
                login = client.post("/api/auth/login", json={"password": os.environ["CIVILTEK_ADMIN_TOKEN"]})
                self.assertEqual(login.status_code, 200)
                self.assertTrue(login.json()["ok"])
                self.assertEqual(client.get("/api/auth/status").json()["authenticated"], True)
                self.assertEqual(client.get("/api/records").status_code, 200)

    if __name__ == "__main__":
        unittest.main()
