import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "input" / "test.pdf").write_bytes(b"")
    (tmp_path / "output" / "test.png").write_bytes(b"")
    import app as flask_app
    # Override module-level path constants so all endpoints use tmp_path
    monkeypatch.setattr(flask_app, "BASE_DIR", tmp_path)
    monkeypatch.setattr(flask_app, "INPUT_DIR", tmp_path / "input")
    monkeypatch.setattr(flask_app, "OUTPUT_DIR", tmp_path / "output")
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


def test_files_lists_pdfs_and_designs(client):
    resp = client.get("/api/files")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "test.pdf" in data["pdfs"]
    assert "test.png" in data["designs"]


def test_pdf_preview_404_for_missing_file(client):
    resp = client.get("/api/pdf-preview/nonexistent.pdf")
    assert resp.status_code == 404
