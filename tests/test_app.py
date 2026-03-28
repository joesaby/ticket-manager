import pytest
import os
import sys
import json
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


def test_detect_qr_404_for_missing_file(client):
    resp = client.get("/api/detect-qr/nonexistent.pdf")
    assert resp.status_code == 404


def test_detect_qr_returns_box_or_empty(client, monkeypatch):
    """detect-qr returns a list (may be empty for a blank PDF)."""
    # app.py uses `from pyzbar import pyzbar` so the live name is pyzbar.pyzbar.decode
    monkeypatch.setattr("pyzbar.pyzbar.decode", lambda img: [])
    resp = client.get("/api/detect-qr/test.pdf")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data["boxes"], list)


def test_generate_writes_ticket_gen_sh(client, tmp_path):
    payload = {
        "pdf": "test.pdf",
        "design": "test.png",
        "qr_x": 100,
        "qr_y": 200,
        "qr_scale": 0.6,
        "start_number": 1,
    }
    resp = client.post("/api/generate",
                       data=json.dumps(payload),
                       content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "script" in data
    assert "input/test.pdf" in data["script"]
    assert "--qr-x 100" in data["script"]
    assert "--qr-y 200" in data["script"]
    assert "--qr-scale 0.6" in data["script"]
    assert "--start-number 1" in data["script"]
    # BASE_DIR is monkeypatched to tmp_path in the client fixture
    sh_path = tmp_path / "ticket_gen.sh"
    assert sh_path.exists()
    assert sh_path.read_text() == data["script"]
