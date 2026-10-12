import sqlite3

from app.api import routes
from app.core.config import get_settings


def test_home_and_liveness(client):
    assert "DeskPilot AI" in client.get("/").text
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_chat_consent_and_audit(client, monkeypatch):
    calls = []

    def fake_ask(question, *, allow_web):
        calls.append((question, allow_web))
        return {
            "answer": "Use the VPN client",
            "source_used": "private_kb",
            "trace": ["Query rewrite → confidential VPN"],
            "citations": [],
            "retry_count": 1,
        }

    monkeypatch.setattr(routes, "ask", fake_ask)
    response = client.post("/api/chat", json={"question": "  VPN support  "})
    assert response.status_code == 200
    assert calls == [("VPN support", False)]
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    with sqlite3.connect(get_settings().audit_db_path) as con:
        row = con.execute(
            "SELECT question, question_hash, trace_json FROM support_events"
        ).fetchone()
    assert row[0] is None and len(row[1]) == 64
    assert "confidential" not in row[2]


def test_empty_question_rejected(client):
    assert client.post("/api/chat", json={"question": "   "}).status_code == 422


def test_provider_errors_are_not_exposed(client, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("secret-provider-key")

    monkeypatch.setattr(routes, "ask", fail)
    response = client.post("/api/chat", json={"question": "VPN help"})
    assert response.status_code == 502
    assert "secret-provider-key" not in response.text
    assert response.headers["X-Request-ID"] in response.text


def test_ingestion_requires_configured_key(client, monkeypatch):
    files = {"file": ("test.md", b"VPN instructions", "text/markdown")}
    assert client.post("/api/ingest", files=files).status_code == 401
    monkeypatch.setattr(get_settings(), "admin_api_key", "")
    assert client.post("/api/ingest", files=files).status_code == 503


def test_ingestion_limits_and_cleanup(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 4)
    response = client.post(
        "/api/ingest",
        headers={"X-Admin-Key": "test-key"},
        files={"file": ("test.md", b"12345", "text/markdown")},
    )
    assert response.status_code == 413
    from pathlib import Path

    assert not list(Path(get_settings().upload_dir).iterdir())


def test_ingestion_rejects_empty_or_unsupported(client):
    headers = {"X-Admin-Key": "test-key"}
    assert (
        client.post("/api/ingest", headers=headers, files={"file": ("test.md", b"")}).status_code
        == 400
    )
    assert (
        client.post(
            "/api/ingest", headers=headers, files={"file": ("script.exe", b"x")}
        ).status_code
        == 400
    )


def test_ingestion_cleans_files_and_preserves_metadata(client, monkeypatch):
    calls = []
    monkeypatch.setattr(routes, "add_documents", lambda chunks: calls.extend(chunks) or ["id"])
    response = client.post(
        "/api/ingest",
        headers={"X-Admin-Key": "test-key"},
        files={"file": ("../../handbook.md", b"Connect through the VPN client.")},
    )
    assert response.status_code == 200
    assert response.json()["file"] == "handbook.md"
    assert calls[0].metadata["source"] == "handbook.md"
    assert len(calls[0].metadata["document_id"]) == 64
    from pathlib import Path

    assert not list(Path(get_settings().upload_dir).iterdir())


def test_parser_failure_cleans_temp_upload(client, monkeypatch):
    def fail(*args):
        raise ValueError("private document contents")

    monkeypatch.setattr(routes, "load_file", fail)
    response = client.post(
        "/api/ingest",
        headers={"X-Admin-Key": "test-key"},
        files={"file": ("bad.pdf", b"not a PDF")},
    )
    assert response.status_code == 502
    assert "private document contents" not in response.text
    from pathlib import Path

    assert not list(Path(get_settings().upload_dir).iterdir())
