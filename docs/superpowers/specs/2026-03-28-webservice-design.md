# Web Service Design — Ticket QR Positioning Tool

**Date:** 2026-03-28
**Status:** Approved

## Overview

A local-only Flask web service that lets a user visually position a QR code box onto a design template, then generates a `ticket_gen.sh` shell script with the correct parameters.

## Goals

- Load a PDF from `input/` and a design template PNG from `output/`
- Render PDF page 1 and auto-detect the QR region
- Let the user drag and resize the QR box on the design template to set placement and padding
- Generate `ticket_gen.sh` with the derived parameters

## Non-Goals

- Multi-ticket-type in one session (one type at a time)
- Deployment / hosting (local only)
- Page navigation (page 1 assumed representative of all pages)

---

## Architecture

```
ticket-manager/
├── app.py                        ← Flask server (new)
├── templates/
│   └── index.html                ← Single-page UI (new)
├── input/                        ← Source PDFs
├── output/                       ← Design template PNGs
├── complete_qr_extractor.py      ← Extended with --qr-x/--qr-y (modified)
└── ticket_gen.sh                 ← Generated output
```

### Flask API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/files` | Lists PDFs in `input/` and PNGs in `output/` |
| `GET` | `/api/pdf-preview/<filename>` | Renders page 1 of PDF as PNG via PyMuPDF, returns image |
| `GET` | `/api/detect-qr/<filename>` | Detects QR on page 1, returns `{x, y, w, h}` in PDF pixel coords |
| `GET` | `/api/design/<filename>` | Serves a design template PNG from `output/` |
| `POST` | `/api/generate` | Writes `ticket_gen.sh` and returns script content |

### POST /api/generate payload

```json
{
  "pdf": "Child_1_50.pdf",
  "design": "Child_sample.png",
  "qr_x": 312,
  "qr_y": 418,
  "qr_scale": 0.6,
  "start_number": 1
}
```

---

## Frontend (Single Page)

### Layout

```
┌─────────────────────────────────────────────┐
│  🎟 Ticket Generator                         │
├─────────────────────────────────────────────┤
│ [PDF ▾] [Design ▾] [Start# ] [Scale ──●──] [Load →] │
├──────────────────┬──────────────────────────┤
│ ① Source PDF     │  ② Design Template       │
│   Page 1 render  │    PNG render             │
│   [QR box auto-  │    [QR box draggable +    │
│    detected,     │     resizable — sets      │
│    adjustable]   │     x, y, scale]          │
│                  │    live x/y readout       │
├──────────────────┴──────────────────────────┤
│ Output: ticket_gen.sh      [⬇ Generate]     │
│ python3 complete_qr_extractor.py ...        │
└─────────────────────────────────────────────┘
```

### Interaction Model

1. User selects PDF and design from dropdowns, sets start number and scale, clicks **Load**
2. Left panel renders PDF page 1; QR box is auto-detected and shown as a purple overlay (draggable to adjust extraction region)
3. Right panel renders design template; QR box appears as a draggable + resizable overlay
   - **Drag** → sets `qr_x`, `qr_y` (top-left of box in design coords)
   - **Resize handles** → adjusts displayed box size, updates `qr_scale`
   - Live coordinate readout shown (e.g., `x:312 y:418`)
4. Click **Generate** → calls `POST /api/generate`, writes `ticket_gen.sh`, shows script preview

### Key UI behaviours

- QR box on design panel is sized proportionally: `base_size * qr_scale`
- Resize handles on corners — dragging updates scale in real time
- Scale slider in top bar and resize handles stay in sync
- Coordinate readout updates on every drag/resize event

---

## Code Changes to `complete_qr_extractor.py`

Add two new CLI parameters:

- `--qr-x INT` — X coordinate (px) of QR box top-left on design template
- `--qr-y INT` — Y coordinate (px) of QR box top-left on design template

When both `--qr-x` and `--qr-y` are provided, skip the `--qr-position` / `--qr-margin` placement logic and place the box at the given absolute coordinates. Existing `--qr-position` behaviour is preserved when `--qr-x`/`--qr-y` are absent.

---

## Generated `ticket_gen.sh` Format

```bash
#!/bin/bash
python3 complete_qr_extractor.py \
  -p input/Child_1_50.pdf \
  -d output/Child_sample.png \
  -o output/Child_tickets.pdf \
  --qr-scale 0.6 \
  --qr-x 312 --qr-y 418 \
  --start-number 1
```

The output PDF filename is derived as `output/<pdf_stem>_tickets.pdf`.

---

## Dependencies

All already present in the project:
- `flask` — web server
- `fitz` (PyMuPDF) — PDF-to-image rendering and QR detection support
- `pyzbar` — QR code detection
- `Pillow` — image handling

No new dependencies required.

---

## Running the Service

```bash
python app.py
# Opens at http://localhost:5000
```
