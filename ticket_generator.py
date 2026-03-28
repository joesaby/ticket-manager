#!/usr/bin/env python3
"""
Ticket Generator
Crops a user-specified region from every page of a source PDF,
scales it, and composites it onto a design template PNG.

Usage:
    python3 ticket_generator.py \
        -p input/tickets.pdf \
        -d output/design.png \
        -o output/tickets_out.pdf \
        --src-x 120 --src-y 80 --src-w 260 --src-h 320 \
        --qr-x 1400 --qr-y 180 \
        --qr-scale 0.85 \
        --start-number 1
"""

import argparse
import io
import os
import sys

import fitz
from PIL import Image, ImageDraw, ImageFont


class TicketGenerator:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def log(self, msg):
        if self.verbose:
            print(f"[INFO] {msg}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _crop_region(self, page, src_x, src_y, src_w, src_h):
        """Crop (src_x, src_y, src_w, src_h) from a PDF page at 2× resolution."""
        clip = fitz.Rect(src_x, src_y, src_x + src_w, src_y + src_h)
        pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(2, 2))
        return pix.tobytes("png")

    def _load_font(self, size):
        for path in [
            "arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    def _draw_counter_on_page(self, out_page, ticket_num, num_x, num_y, font_size=48):
        """Render the ticket number as an image and place it at (num_x, num_y) on the page."""
        text = f"{ticket_num:03d}"
        font = self._load_font(font_size)

        # Measure
        tmp = Image.new("RGBA", (1, 1))
        bbox = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Render onto transparent background
        pad = 4
        img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            draw.text((pad + dx, pad + dy), text, font=font, fill=(180, 180, 180, 255))
        draw.text((pad, pad), text, font=font, fill=(0, 0, 0, 255))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        rect = fitz.Rect(num_x, num_y, num_x + tw + pad * 2, num_y + th + pad * 2)
        out_page.insert_image(rect, stream=buf.read(), overlay=True)
        self.log(f"  counter {text} at ({num_x}, {num_y})")

    def _place_on_page(self, out_page, img_bytes, qr_x, qr_y, qr_scale):
        """Scale img_bytes and overlay it at (qr_x, qr_y) on out_page."""
        img = Image.open(io.BytesIO(img_bytes))
        new_w = max(1, int(img.width * qr_scale))
        new_h = max(1, int(img.height * qr_scale))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        rect = fitz.Rect(qr_x, qr_y, qr_x + new_w, qr_y + new_h)
        out_page.insert_image(rect, stream=buf.read(), overlay=True)
        self.log(f"  placed at ({qr_x}, {qr_y})  final size {new_w}×{new_h}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        pdf_path,
        design_path,
        output_path,
        src_x, src_y, src_w, src_h,
        qr_x, qr_y,
        qr_scale=1.0,
        start_number=1,
        num_x=None, num_y=None,
        num_font_size=48,
    ):
        doc = fitz.open(pdf_path)
        design = Image.open(design_path).convert("RGBA")
        dw, dh = design.size
        self.log(f"Design: {dw}×{dh}  |  source region: ({src_x},{src_y}) {src_w}×{src_h}")

        # Pre-render design to bytes once
        design_buf = io.BytesIO()
        design.save(design_buf, format="PNG")
        design_bytes = design_buf.getvalue()

        output_doc = fitz.open()
        total = 0

        for page_num in range(len(doc)):
            self.log(f"Page {page_num + 1}/{len(doc)}")
            page = doc[page_num]

            crop_bytes = self._crop_region(page, src_x, src_y, src_w, src_h)
            ticket_num = start_number + total
            total += 1

            out_page = output_doc.new_page(width=dw, height=dh)
            out_page.insert_image(out_page.rect, stream=design_bytes, overlay=False)
            self._place_on_page(out_page, crop_bytes, qr_x, qr_y, qr_scale)

            if num_x is not None and num_y is not None:
                self._draw_counter_on_page(out_page, ticket_num, num_x, num_y, num_font_size)

        output_doc.save(output_path)
        output_doc.close()
        doc.close()
        print(f"✅  {total} tickets → {output_path}")
        return total


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Crop a region from each PDF page and place it on a design template."
    )
    p.add_argument("-p", "--pdf",    required=True, help="Source PDF")
    p.add_argument("-d", "--design", required=True, help="Design template PNG")
    p.add_argument("-o", "--output", required=True, help="Output PDF")

    p.add_argument("--src-x", type=int, required=True, help="Source region left edge (PDF pts)")
    p.add_argument("--src-y", type=int, required=True, help="Source region top edge (PDF pts)")
    p.add_argument("--src-w", type=int, required=True, help="Source region width (PDF pts)")
    p.add_argument("--src-h", type=int, required=True, help="Source region height (PDF pts)")

    p.add_argument("--qr-x",     type=int,   required=True, help="Placement X on design (px)")
    p.add_argument("--qr-y",     type=int,   required=True, help="Placement Y on design (px)")
    p.add_argument("--qr-scale", type=float, default=1.0,   help="Scale factor (default 1.0)")
    p.add_argument("--start-number", type=int, default=1,   help="First ticket number (default 1)")
    p.add_argument("--num-x", type=int, default=None, help="Counter number X on design (px)")
    p.add_argument("--num-y", type=int, default=None, help="Counter number Y on design (px)")
    p.add_argument("--num-font-size", type=int, default=48, help="Counter font size (default 48)")
    p.add_argument("-v", "--verbose", action="store_true")

    args = p.parse_args()

    for path, label in [(args.pdf, "PDF"), (args.design, "Design")]:
        if not os.path.exists(path):
            print(f"Error: {label} not found: {path}")
            sys.exit(1)

    if args.qr_scale <= 0:
        print("Error: --qr-scale must be positive")
        sys.exit(1)

    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    try:
        gen = TicketGenerator(verbose=args.verbose)
        gen.process(
            args.pdf, args.design, args.output,
            args.src_x, args.src_y, args.src_w, args.src_h,
            args.qr_x, args.qr_y,
            qr_scale=args.qr_scale,
            start_number=args.start_number,
            num_x=args.num_x,
            num_y=args.num_y,
            num_font_size=args.num_font_size,
        )
    except Exception as e:
        print(f"❌  {e}")
        if args.verbose:
            import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
