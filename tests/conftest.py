import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "audit_db_path", str(tmp_path / "audit.db"))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "admin_api_key", "test-key")
    monkeypatch.setattr(settings, "enable_web_search", False)
    monkeypatch.setattr(settings, "audit_store_questions", False)
    with TestClient(app) as test_client:
        yield test_client
