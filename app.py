import os
import io
import base64
import json
from pathlib import Path

import cv2
import numpy as np
import fitz
from flask import Flask, jsonify, request, send_file, abort, render_template
from pyzbar import pyzbar

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
    # Prevent path traversal
    if not pdf_path.resolve().is_relative_to(INPUT_DIR.resolve()):
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
    # Prevent path traversal
    if not design_path.resolve().is_relative_to(OUTPUT_DIR.resolve()):
        abort(404)
    return send_file(str(design_path), mimetype="image/png")


@app.route("/api/detect-qr/<filename>")
def detect_qr(filename):
    pdf_path = INPUT_DIR / filename
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        abort(404)
    # Prevent path traversal
    if not pdf_path.resolve().is_relative_to(INPUT_DIR.resolve()):
        abort(404)

    try:
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
    except Exception:
        return jsonify({"boxes": []})


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    pdf = data["pdf"]
    design = data["design"]

    allowed_pdfs = {f.name for f in INPUT_DIR.glob("*.pdf")}
    allowed_designs = {f.name for f in OUTPUT_DIR.glob("*.png")}
    if pdf not in allowed_pdfs or design not in allowed_designs:
        abort(400)

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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
