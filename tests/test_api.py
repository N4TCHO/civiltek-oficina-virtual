import importlib
import io
import os
from pathlib import Path

from fastapi.testclient import TestClient
from docx import Document


def test_health_auth_records_and_docx(tmp_path, monkeypatch):
    monkeypatch.setenv("CIVILTEK_ADMIN_TOKEN", "test-secret-token-of-at-least-32-characters")
    monkeypatch.setenv("CIVILTEK_DB_PATH", str(tmp_path / "civiltek.db"))
    import backend.main as module
    module = importlib.reload(module)
    with TestClient(module.app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["ok"] is True
        assert client.get("/api/records").status_code == 401
        headers = {"Authorization": "Bearer test-secret-token-of-at-least-32-characters"}
        response = client.post("/api/records", headers=headers, json={
            "kind": "project", "title": "Obra piloto", "payload": {"details": "Prueba"}
        })
        assert response.status_code == 200
        record_id = response.json()["id"]
        items = client.get("/api/records", headers=headers)
        assert items.status_code == 200
        assert items.json()[0]["title"] == "Obra piloto"
        update = client.put(f"/api/records/{record_id}", headers=headers, json={
            "kind": "project", "title": "Obra revisada", "payload": {}
        })
        assert update.status_code == 200
        doc = client.post("/api/letters/docx", headers=headers, json={
            "number": "193", "date": "2026-10-12", "recipient": "Inspector Fiscal",
            "subject": "Presentación", "body": "De nuestra consideración:",
            "signer": "Encargado de Calidad"
        })
        assert doc.status_code == 200
        word = Document(io.BytesIO(doc.content))
        assert "CARTA N.º 193" in "\n".join(p.text for p in word.paragraphs)
        assert client.delete(f"/api/records/{record_id}", headers=headers).status_code == 200
        assert client.get("/api/records", headers=headers).json() == []


def test_missing_secret_blocks_access(tmp_path, monkeypatch):
    monkeypatch.delenv("CIVILTEK_ADMIN_TOKEN", raising=False)
    monkeypatch.setenv("CIVILTEK_DB_PATH", str(tmp_path / "empty.db"))
    import backend.main as module
    module = importlib.reload(module)
    with TestClient(module.app) as client:
        assert client.get("/api/records").status_code == 503
