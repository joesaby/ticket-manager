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
