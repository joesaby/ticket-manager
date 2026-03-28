# Ticket QR Positioning Web Service Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Flask web service that lets a user visually drag and resize a QR box onto a design template, then generates `ticket_gen.sh` with the correct placement parameters.

**Architecture:** Flask backend serves a single-page HTML UI. PyMuPDF renders PDF page 1 as a PNG for preview. pyzbar detects the QR region. The frontend uses mouse events for drag-and-drop and resize on the design template panel, converting display coordinates to native pixel coordinates before POSTing to the generate endpoint.

**Tech Stack:** Python 3, Flask, PyMuPDF (fitz), pyzbar, Pillow, vanilla HTML/JS/CSS (no build step)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `complete_qr_extractor.py` | Modify | Add `--qr-x` / `--qr-y` CLI params; absolute placement path |
| `app.py` | Create | Flask server — all API endpoints |
| `templates/index.html` | Create | Single-page UI — file selection, two-panel canvas, generate |
| `requirements.txt` | Create | Pin flask + existing deps |
| `tests/test_app.py` | Create | API endpoint tests |
| `tests/test_extractor_placement.py` | Create | Tests for new `--qr-x/--qr-y` placement logic |

---

## Chunk 1: Backend

### Task 1: Add `--qr-x` / `--qr-y` to the extractor

**Files:**
- Modify: `complete_qr_extractor.py`
- Create: `tests/test_extractor_placement.py`

- [ ] **Step 1: Create test file for new placement logic**

```bash
mkdir -p tests
```

Create `tests/test_extractor_placement.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from complete_qr_extractor import CompleteQRExtractor


def test_absolute_position_used_when_qr_xy_provided():
    """When qr_x and qr_y are given, box is placed at those exact coords."""
    extractor = CompleteQRExtractor()

    positions = []

    def capture_rect(rect, stream, overlay):
        positions.append((rect.x0, rect.y0))

    mock_page = MagicMock()
    mock_page.rect = MagicMock(width=800, height=600)
    mock_page.insert_image = capture_rect

    # Minimal box image (1x1 white pixel PNG)
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (60, 70), "white").save(buf, format="PNG")
    box_image_bytes = buf.getvalue()

    extractor._place_box_on_page(mock_page, box_image_bytes, qr_scale=1.0, qr_x=100, qr_y=200)

    assert len(positions) == 1
    assert positions[0] == (100, 200)


def test_margin_position_used_when_no_qr_xy():
    """When qr_x/qr_y are absent, falls back to margin-based right placement."""
    extractor = CompleteQRExtractor()

    positions = []

    def capture_rect(rect, stream, overlay):
        positions.append((rect.x0, rect.y0))

    mock_page = MagicMock()
    mock_page.rect = MagicMock(width=800, height=600)
    mock_page.insert_image = capture_rect

    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (60, 70), "white").save(buf, format="PNG")
    box_image_bytes = buf.getvalue()

    extractor._place_box_on_page(mock_page, box_image_bytes, qr_scale=1.0,
                                  qr_position='right', qr_margin=20,
                                  design_width=800, design_height=600)

    assert len(positions) == 1
    x, y = positions[0]
    # right margin: x = 800 - 60 - 20 = 720
    assert x == 720
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd /Users/josesebastian/git/ticket-manager
python -m pytest tests/test_extractor_placement.py -v
```

Expected: `AttributeError` or `ImportError` — `_place_box_on_page` does not exist yet.

- [ ] **Step 3: Refactor placement into `_place_box_on_page` and add `--qr-x`/`--qr-y` to CLI**

In `complete_qr_extractor.py`, add this method to `CompleteQRExtractor` (after `mask_awaiting_payment`):

```python
def _place_box_on_page(self, page, box_image_bytes, qr_scale=1.0,
                        qr_x=None, qr_y=None,
                        qr_position='right', qr_margin=20,
                        design_width=None, design_height=None):
    """Place a QR box image onto a page. Uses absolute coords if qr_x/qr_y given."""
    import io
    box_img = Image.open(io.BytesIO(box_image_bytes))
    new_width = int(box_img.width * qr_scale)
    new_height = int(box_img.height * qr_scale)
    box_img = box_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    if qr_x is not None and qr_y is not None:
        box_x, box_y = qr_x, qr_y
    else:
        dw = design_width or page.rect.width
        dh = design_height or page.rect.height
        if qr_position == 'left':
            box_x = qr_margin
        else:  # right
            box_x = dw - new_width - qr_margin
        box_y = dh - new_height - qr_margin
        box_x = max(0, box_x)
        box_y = max(0, box_y)

    buf = io.BytesIO()
    box_img.save(buf, format='PNG')
    buf.seek(0)
    box_rect = fitz.Rect(box_x, box_y, box_x + new_width, box_y + new_height)
    page.insert_image(box_rect, stream=buf.read(), overlay=True)
    self.log(f"  Placed QR box at ({box_x}, {box_y}) size: {new_width}x{new_height}")
```

Then, in `process_pdf`, update the signature to accept `qr_x=None, qr_y=None`, and replace the block that starts at `# Load and scale QR box image` with:

```python
# Load QR box bytes; apply mask if needed
box_image_bytes = box['image']
if mask_awaiting or start_number is not None:
    ticket_num = start_number + total_tickets - 1 if start_number is not None else None
    masked = self.mask_awaiting_payment(Image.open(io.BytesIO(box_image_bytes)), ticket_num)
    buf = io.BytesIO()
    masked.save(buf, format='PNG')
    box_image_bytes = buf.getvalue()

if qr_x is not None and qr_y is not None:
    self._place_box_on_page(new_page, box_image_bytes,
                            qr_scale=qr_scale, qr_x=qr_x, qr_y=qr_y)
else:
    positions_to_place = []
    if qr_position == 'left':
        positions_to_place.append('left')
    elif qr_position == 'right':
        positions_to_place.append('right')
    elif qr_position == 'both':
        positions_to_place.extend(['left', 'right'])
    for pos in positions_to_place:
        self._place_box_on_page(new_page, box_image_bytes,
                                qr_scale=qr_scale, qr_position=pos,
                                qr_margin=qr_margin,
                                design_width=design_width,
                                design_height=design_height)

if start_number is not None:
    self.log(f"  Added ticket number: {ticket_num:03d} in QR box")
```

Remove the old `box_img = Image.open(...)`, `mask_awaiting_payment` call, `box_img.resize(...)`, `positions_to_place` list, and the `for position in positions_to_place` loop entirely — they are now replaced by the block above.

In `main()`, add to argparse:

```python
parser.add_argument('--qr-x', type=int, default=None,
                   help='Absolute X coordinate for QR box on design (overrides --qr-position)')
parser.add_argument('--qr-y', type=int, default=None,
                   help='Absolute Y coordinate for QR box on design (overrides --qr-position)')
```

Pass `qr_x=args.qr_x, qr_y=args.qr_y` in the `processor.process_pdf(...)` call.

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_extractor_placement.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add complete_qr_extractor.py tests/test_extractor_placement.py
git commit -m "feat: add --qr-x/--qr-y absolute placement to extractor"
```

---

### Task 2: Create `requirements.txt`

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Check installed versions**

```bash
python -m pip show flask pymupdf pyzbar pillow opencv-python numpy | grep -E "^(Name|Version)"
```

- [ ] **Step 2: Write requirements.txt**

Create `requirements.txt` with the versions printed above, e.g.:

```
flask>=2.0
PyMuPDF>=1.23
pyzbar>=0.1.9
Pillow>=9.0
opencv-python>=4.8
numpy>=1.24
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add requirements.txt with flask"
```

---

### Task 3: Flask app — file listing and PDF preview endpoints

**Files:**
- Create: `app.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Write failing tests for `/api/files` and `/api/pdf-preview`**

Create `tests/test_app.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_app.py -v
```

Expected: `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Create `app.py` with file listing and preview endpoints**

```python
import os
import io
import base64
import json
from pathlib import Path

import fitz
from flask import Flask, jsonify, request, send_file, abort, render_template

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/files")
def list_files():
    pdfs = sorted(f.name for f in INPUT_DIR.glob("*.pdf") if f.is_file())
    designs = sorted(f.name for f in OUTPUT_DIR.glob("*.png") if f.is_file())
    return jsonify({"pdfs": pdfs, "designs": designs})


@app.route("/api/pdf-preview/<filename>")
def pdf_preview(filename):
    pdf_path = INPUT_DIR / filename
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        abort(404)
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    doc.close()
    return send_file(io.BytesIO(pix.tobytes("png")), mimetype="image/png")


@app.route("/api/design/<filename>")
def design_image(filename):
    design_path = OUTPUT_DIR / filename
    if not design_path.exists() or design_path.suffix.lower() != ".png":
        abort(404)
    return send_file(str(design_path), mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_app.py::test_files_lists_pdfs_and_designs tests/test_app.py::test_pdf_preview_404_for_missing_file -v
```

Expected: both PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: flask app with file listing and PDF preview endpoints"
```

---

### Task 4: QR detection endpoint

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app.py`

- [ ] **Step 1: Add failing test for `/api/detect-qr`**

Append to `tests/test_app.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_app.py::test_detect_qr_404_for_missing_file tests/test_app.py::test_detect_qr_returns_box_or_empty -v
```

Expected: FAIL — endpoint does not exist.

- [ ] **Step 3: Add detect-qr endpoint to `app.py`**

Add imports at top of `app.py`:
```python
import cv2
import numpy as np
from pyzbar import pyzbar
```

Add endpoint after `design_image`:
```python
@app.route("/api/detect-qr/<filename>")
def detect_qr(filename):
    pdf_path = INPUT_DIR / filename
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        abort(404)

    doc = fitz.open(str(pdf_path))
    page = doc[0]
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    doc.close()

    img_data = pix.tobytes("png")
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    decoded = pyzbar.decode(gray)
    if not decoded:
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        decoded = pyzbar.decode(binary)

    boxes = []
    for qr in decoded:
        x, y, w, h = qr.rect
        boxes.append({
            "x": x // 2,
            "y": y // 2,
            "w": w // 2,
            "h": h // 2,
        })

    return jsonify({"boxes": boxes})
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_app.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: add QR detection endpoint"
```

---

### Task 5: Generate endpoint

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app.py`

- [ ] **Step 1: Add failing test for `POST /api/generate`**

Append to `tests/test_app.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/test_app.py::test_generate_writes_ticket_gen_sh -v
```

Expected: FAIL — endpoint does not exist.

- [ ] **Step 3: Add generate endpoint to `app.py`**

```python
@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    pdf = data["pdf"]
    design = data["design"]
    qr_x = int(data["qr_x"])
    qr_y = int(data["qr_y"])
    qr_scale = float(data["qr_scale"])
    start_number = int(data["start_number"])

    pdf_stem = Path(pdf).stem
    output_pdf = f"output/{pdf_stem}_tickets.pdf"

    script = (
        f"#!/bin/bash\n"
        f"python3 complete_qr_extractor.py \\\n"
        f"  -p input/{pdf} \\\n"
        f"  -d output/{design} \\\n"
        f"  -o {output_pdf} \\\n"
        f"  --qr-scale {qr_scale} \\\n"
        f"  --qr-x {qr_x} --qr-y {qr_y} \\\n"
        f"  --start-number {start_number}\n"
    )

    sh_path = BASE_DIR / "ticket_gen.sh"
    sh_path.write_text(script)
    sh_path.chmod(0o755)

    return jsonify({"script": script})
```

- [ ] **Step 4: Run all backend tests**

```bash
python -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: add generate endpoint that writes ticket_gen.sh"
```

---

## Chunk 2: Frontend

### Task 6: Base HTML — file selectors and Load button

**Files:**
- Create: `templates/index.html`

- [ ] **Step 1: Create `templates/` directory**

```bash
mkdir -p templates
```

- [ ] **Step 2: Create `templates/index.html` with selectors and Load**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ticket Generator</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f172a; color: #e2e8f0; font-family: system-ui, sans-serif; min-height: 100vh; }

  header { background: #1e293b; padding: 12px 20px; border-bottom: 1px solid #334155; font-weight: 700; font-size: 16px; }

  #controls { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; padding: 14px 20px; border-bottom: 1px solid #1e293b; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
  select, input[type=number], input[type=range] { background: #1e293b; border: 1px solid #334155; border-radius: 5px; padding: 7px 10px; color: #e2e8f0; font-size: 13px; }
  input[type=range] { padding: 0; width: 110px; accent-color: #7c3aed; }
  #scaleVal { font-size: 12px; color: #94a3b8; margin-left: 4px; }

  button { padding: 8px 18px; border: none; border-radius: 5px; font-size: 13px; font-weight: 600; cursor: pointer; }
  #btnLoad { background: #7c3aed; color: white; }
  #btnLoad:hover { background: #6d28d9; }
  #btnGenerate { background: #22c55e; color: white; font-size: 14px; padding: 9px 24px; }
  #btnGenerate:disabled { background: #374151; color: #6b7280; cursor: not-allowed; }

  #canvas-row { display: flex; gap: 16px; padding: 16px 20px; }
  .panel { flex: 1; }
  .panel-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .panel-frame { background: #1e293b; border-radius: 6px; border: 1px solid #334155; overflow: hidden; position: relative; min-height: 300px; display: flex; align-items: center; justify-content: center; }
  .panel-frame img { max-width: 100%; display: block; user-select: none; }
  .arrow { display: flex; align-items: center; color: #7c3aed; font-size: 24px; padding-top: 28px; }

  #footer { padding: 12px 20px; border-top: 1px solid #1e293b; display: flex; align-items: center; justify-content: space-between; }
  #footer .label { font-size: 12px; color: #64748b; }

  #script-preview { margin: 0 20px 16px; background: #0a0a0a; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 12px; color: #22c55e; border: 1px solid #1e293b; white-space: pre-wrap; display: none; }

  #coords { font-size: 11px; color: #94a3b8; background: rgba(0,0,0,0.6); padding: 2px 6px; border-radius: 3px; position: absolute; bottom: 6px; left: 8px; pointer-events: none; }
  #status { font-size: 12px; color: #f59e0b; margin-left: 12px; }
</style>
</head>
<body>

<header>🎟 Ticket Generator</header>

<div id="controls">
  <div class="field">
    <label>PDF (input/)</label>
    <select id="selPdf"><option value="">— select —</option></select>
  </div>
  <div class="field">
    <label>Design (output/)</label>
    <select id="selDesign"><option value="">— select —</option></select>
  </div>
  <div class="field">
    <label>Start #</label>
    <input type="number" id="inpStart" value="1" min="1" style="width:80px">
  </div>
  <div class="field">
    <label>QR Scale <span id="scaleVal">0.60×</span></label>
    <input type="range" id="sldScale" min="0.2" max="2.0" step="0.05" value="0.6">
  </div>
  <button id="btnLoad">Load →</button>
  <span id="status"></span>
</div>

<div id="canvas-row">
  <div class="panel">
    <div class="panel-label">① Source — PDF page 1</div>
    <div class="panel-frame" id="pdfFrame">
      <span style="color:#475569;font-size:13px;">Select a PDF and click Load</span>
    </div>
  </div>
  <div class="arrow">→</div>
  <div class="panel">
    <div class="panel-label">② Target — Design template</div>
    <div class="panel-frame" id="designFrame">
      <span style="color:#475569;font-size:13px;">Select a design and click Load</span>
    </div>
  </div>
</div>

<div id="footer">
  <span class="label">Output: <strong>ticket_gen.sh</strong></span>
  <button id="btnGenerate" disabled>⬇ Generate ticket_gen.sh</button>
</div>
<pre id="script-preview"></pre>

<script>
// ---------- populate dropdowns ----------
fetch('/api/files').then(r => r.json()).then(data => {
  const pdfSel = document.getElementById('selPdf');
  const dsnSel = document.getElementById('selDesign');
  data.pdfs.forEach(f => {
    const o = document.createElement('option'); o.value = f; o.textContent = f; pdfSel.appendChild(o);
  });
  data.designs.forEach(f => {
    const o = document.createElement('option'); o.value = f; o.textContent = f; dsnSel.appendChild(o);
  });
});

// ---------- scale slider ----------
const sldScale = document.getElementById('sldScale');
const scaleVal = document.getElementById('scaleVal');
sldScale.addEventListener('input', () => {
  scaleVal.textContent = parseFloat(sldScale.value).toFixed(2) + '×';
  if (window.qrOverlay) updateOverlaySize();
});

// ---------- load ----------
document.getElementById('btnLoad').addEventListener('click', loadFiles);

async function loadFiles() {
  const pdf = document.getElementById('selPdf').value;
  const design = document.getElementById('selDesign').value;
  if (!pdf || !design) { alert('Select both a PDF and a design first.'); return; }

  const status = document.getElementById('status');
  status.textContent = 'Loading…';

  // Load PDF preview
  const pdfFrame = document.getElementById('pdfFrame');
  pdfFrame.innerHTML = '';
  const pdfImg = document.createElement('img');
  pdfImg.src = '/api/pdf-preview/' + encodeURIComponent(pdf) + '?t=' + Date.now();
  pdfImg.alt = 'PDF page 1';
  pdfFrame.appendChild(pdfImg);

  // Load design
  const designFrame = document.getElementById('designFrame');
  designFrame.innerHTML = '';
  const dsnImg = document.createElement('img');
  dsnImg.id = 'designImg';
  dsnImg.src = '/api/design/' + encodeURIComponent(design) + '?t=' + Date.now();
  dsnImg.alt = 'Design template';
  designFrame.appendChild(dsnImg);

  // Once design loaded, detect QR and setup overlay
  await Promise.all([
    new Promise(r => { pdfImg.onload = r; pdfImg.onerror = r; }),
    new Promise(r => { dsnImg.onload = r; dsnImg.onerror = r; }),
  ]);

  // Detect QR and show source overlay (read-only)
  detectAndShowSourceQR(pdf, pdfFrame, pdfImg);

  // Setup draggable overlay on design
  setupDesignOverlay(designFrame, dsnImg);

  document.getElementById('btnGenerate').disabled = false;
  status.textContent = '';
}
</script>
<!-- drag-and-drop logic added in Task 7 -->
</body>
</html>
```

- [ ] **Step 3: Smoke test manually**

```bash
python app.py
```

Open `http://localhost:5000`. You should see the UI with dropdowns populated from `input/` and `output/`. Load button should load images into both panels. Note: clicking Load will log console errors (`detectAndShowSourceQR is not defined`, `setupDesignOverlay is not defined`) — this is expected since the drag-and-drop script is added in Task 7. The images should still render correctly.

- [ ] **Step 4: Commit**

```bash
git add templates/index.html
git commit -m "feat: base HTML UI with file selectors and load"
```

---

### Task 7: Source QR overlay and drag-and-drop on design panel

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: Add source QR overlay function**

Replace the `<!-- drag-and-drop logic added in Task 7 -->` comment in `templates/index.html` with:

```html
<script>
// -------- Source panel: read-only QR overlay --------
async function detectAndShowSourceQR(pdf, frame, imgEl) {
  const resp = await fetch('/api/detect-qr/' + encodeURIComponent(pdf));
  const data = await resp.json();
  if (!data.boxes || data.boxes.length === 0) return;

  const box = data.boxes[0];
  // PDF preview image is rendered at 2x then served as PNG.
  // The img element displays it scaled to fit. Compute display scale.
  // detect-qr already returns coords in original (1x) PDF pixel space (it divides by 2).
  // We only need to scale from native pixels to display pixels.
  const scaleX = imgEl.clientWidth / imgEl.naturalWidth;
  const scaleY = imgEl.clientHeight / imgEl.naturalHeight;

  const div = document.createElement('div');
  div.style.cssText = `
    position:absolute;
    left:${box.x * scaleX}px;
    top:${box.y * scaleY}px;
    width:${box.w * scaleX}px;
    height:${box.h * scaleY}px;
    border:2px solid #7c3aed;
    background:rgba(124,58,237,0.1);
    border-radius:3px;
    pointer-events:none;
  `;
  const lbl = document.createElement('span');
  lbl.textContent = 'auto-detected ✓';
  lbl.style.cssText = 'position:absolute;top:-18px;left:0;font-size:9px;color:#7c3aed;font-weight:600;white-space:nowrap;';
  div.appendChild(lbl);
  frame.style.position = 'relative';
  frame.appendChild(div);
}

// -------- Design panel: draggable + resizable overlay --------
window.qrOverlay = null;   // the overlay element
window.designNativeW = 0;
window.designNativeH = 0;

function setupDesignOverlay(frame, imgEl) {
  window.designNativeW = imgEl.naturalWidth;
  window.designNativeH = imgEl.naturalHeight;

  frame.style.position = 'relative';

  // Create overlay box
  const box = document.createElement('div');
  box.id = 'qrBox';
  const scale = parseFloat(document.getElementById('sldScale').value);
  // Initial size: 80px display, positioned bottom-right
  const initW = 80, initH = 90;
  box.style.cssText = `
    position:absolute;
    width:${initW}px;height:${initH}px;
    right:14px;bottom:14px;
    border:2px dashed #f59e0b;
    background:rgba(245,158,11,0.15);
    border-radius:4px;
    cursor:move;
    user-select:none;
  `;

  // Resize handle (bottom-right corner)
  const handle = document.createElement('div');
  handle.style.cssText = `
    position:absolute;right:-4px;bottom:-4px;
    width:10px;height:10px;
    background:#f59e0b;border-radius:2px;
    cursor:se-resize;
  `;
  box.appendChild(handle);

  // Coords readout
  const coords = document.createElement('div');
  coords.id = 'coords';
  coords.textContent = '';
  frame.appendChild(coords);

  frame.appendChild(box);
  window.qrOverlay = box;

  makeDraggable(box, frame, handle, imgEl, coords);
}

function updateOverlaySize() {
  // Called when scale slider changes after overlay is set up.
  // Resizes the box proportionally and updates the coord readout.
  const box = window.qrOverlay;
  if (!box) return;
  const baseW = 80; // same base used when overlay was created
  const baseH = 90;
  const scale = parseFloat(document.getElementById('sldScale').value);
  box.style.width = Math.round(baseW * scale) + 'px';
  box.style.height = Math.round(baseH * scale) + 'px';
  updateCoords(box, document.getElementById('coords'));
}

function updateCoords(box, coordsEl) {
  const frame = box.parentElement;
  const imgEl = frame.querySelector('img');
  if (!imgEl) return;
  const scaleX = imgEl.naturalWidth / imgEl.clientWidth;
  const scaleY = imgEl.naturalHeight / imgEl.clientHeight;

  const x = Math.round(box.offsetLeft * scaleX);
  const y = Math.round(box.offsetTop * scaleY);
  coordsEl.textContent = `x:${x} y:${y}`;
}

function makeDraggable(box, frame, handle, imgEl, coordsEl) {
  let dragState = null;

  box.addEventListener('mousedown', e => {
    if (e.target === handle) return; // handled separately
    e.preventDefault();
    const fr = frame.getBoundingClientRect();
    dragState = {
      type: 'drag',
      startX: e.clientX - box.offsetLeft,
      startY: e.clientY - box.offsetTop,
      frameRect: fr,
    };
  });

  handle.addEventListener('mousedown', e => {
    e.preventDefault();
    e.stopPropagation();
    dragState = {
      type: 'resize',
      startX: e.clientX,
      startY: e.clientY,
      startW: box.offsetWidth,
      startH: box.offsetHeight,
    };
  });

  document.addEventListener('mousemove', e => {
    if (!dragState) return;
    if (dragState.type === 'drag') {
      const fr = dragState.frameRect;
      let x = e.clientX - dragState.startX;
      let y = e.clientY - dragState.startY;
      // Clamp within frame
      x = Math.max(0, Math.min(x, fr.width - box.offsetWidth));
      y = Math.max(0, Math.min(y, fr.height - box.offsetHeight));
      box.style.left = x + 'px';
      box.style.top = y + 'px';
      box.style.right = 'auto';
      box.style.bottom = 'auto';
    } else {
      const dw = e.clientX - dragState.startX;
      const dh = e.clientY - dragState.startY;
      const newW = Math.max(20, dragState.startW + dw);
      const newH = Math.max(20, dragState.startH + dh);
      box.style.width = newW + 'px';
      box.style.height = newH + 'px';
      // Update scale slider to reflect new size relative to original
      const baseW = 80;
      const newScale = (newW / baseW).toFixed(2);
      document.getElementById('sldScale').value = newScale;
      document.getElementById('scaleVal').textContent = newScale + '×';
    }
    updateCoords(box, coordsEl);
  });

  document.addEventListener('mouseup', () => { dragState = null; });
}
</script>
```

- [ ] **Step 2: Smoke test manually**

```bash
python app.py
```

Open `http://localhost:5000`. Select `Child_1_50.pdf` and `Child_sample.png`, click Load. Verify:
- Left panel shows PDF page 1 with a purple QR detection box
- Right panel shows design with a yellow dashed draggable box
- Drag the yellow box around — it should move freely within the panel
- Drag the bottom-right corner handle — box resizes and scale slider updates
- `x:NNN y:NNN` coords shown in corner of design panel

- [ ] **Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: QR detection overlay and drag-and-drop on design panel"
```

---

### Task 8: Generate button — POST and script preview

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: Add generate handler inside the existing `<script>` block in `templates/index.html`**

Find the closing `</script>` of the first script block (after `status.textContent = '';`) and add before it:

```javascript
// -------- Generate --------
document.getElementById('btnGenerate').addEventListener('click', async () => {
  const pdf = document.getElementById('selPdf').value;
  const design = document.getElementById('selDesign').value;
  const startNumber = parseInt(document.getElementById('inpStart').value, 10);
  const qrScale = parseFloat(document.getElementById('sldScale').value);

  const box = document.getElementById('qrBox');
  const imgEl = document.getElementById('designImg');
  if (!box || !imgEl) { alert('Load files first.'); return; }

  // Convert display coords → native pixel coords
  const scaleX = imgEl.naturalWidth / imgEl.clientWidth;
  const scaleY = imgEl.naturalHeight / imgEl.clientHeight;
  const qrX = Math.round(box.offsetLeft * scaleX);
  const qrY = Math.round(box.offsetTop * scaleY);

  const resp = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pdf, design, qr_x: qrX, qr_y: qrY, qr_scale: qrScale, start_number: startNumber }),
  });

  const data = await resp.json();
  const preview = document.getElementById('script-preview');
  preview.textContent = data.script;
  preview.style.display = 'block';
});
```

- [ ] **Step 2: Smoke test end-to-end**

```bash
python app.py
```

1. Open `http://localhost:5000`
2. Select PDF and design, click Load
3. Drag QR box to desired position on design panel
4. Click Generate
5. Check script preview appears with correct x/y/scale values
6. Verify `ticket_gen.sh` was written to project root:

```bash
cat ticket_gen.sh
```

Expected output like:
```bash
#!/bin/bash
python3 complete_qr_extractor.py \
  -p input/Child_1_50.pdf \
  -o output/Child_1_50_tickets.pdf \
  -d output/Child_sample.png \
  --qr-scale 0.6 \
  --qr-x 312 --qr-y 418 \
  --start-number 1
```

- [ ] **Step 3: Run full test suite**

```bash
python -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 4: Final commit**

```bash
git add templates/index.html
git commit -m "feat: generate button posts to API and shows ticket_gen.sh preview"
```
