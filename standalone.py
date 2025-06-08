#!/usr/bin/env python3
"""
Ticket Design Overlay Tool - Command Line Interface
Overlays custom designs on ticket PDFs while preserving QR codes.

Usage:
    python ticket_overlay.py -p tickets.pdf -d design.png -o output.pdf
"""

import argparse
import sys
import os
from pathlib import Path
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageDraw
from pyzbar import pyzbar


class SimpleTicketOverlay:
    def __init__(self, verbose=False):
        self.verbose = verbose
        
    def log(self, message):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[INFO] {message}")
    
    def detect_qr_codes(self, image_path):
        """Detect QR codes in an image"""
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            img = cv2.imdecode(np.frombuffer(image_path, np.uint8), cv2.IMREAD_COLOR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect QR codes
        qr_codes = []
        decoded = pyzbar.decode(gray)
        
        for qr in decoded:
            x, y, w, h = qr.rect
            qr_codes.append({
                'x': x,
                'y': y,
                'width': w,
                'height': h,
                'data': qr.data.decode('utf-8') if qr.data else ''
            })
            self.log(f"Found QR code at ({x}, {y}) with size {w}x{h}")
        
        # If no QR codes found, try with preprocessing
        if not qr_codes:
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            decoded = pyzbar.decode(binary)
            
            for qr in decoded:
                x, y, w, h = qr.rect
                qr_codes.append({
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'data': qr.data.decode('utf-8') if qr.data else ''
                })
                self.log(f"Found QR code (preprocessed) at ({x}, {y})")
        
        return qr_codes
    
    def process_pdf(self, pdf_path, design_path, output_path, opacity=0.7, padding=15):
        """Main processing function"""
        self.log(f"Opening PDF: {pdf_path}")
        doc = fitz.open(pdf_path)
        
        self.log(f"Loading design: {design_path}")
        design = Image.open(design_path).convert('RGBA')
        
        total_pages = len(doc)
        self.log(f"Processing {total_pages} pages")
        
        for page_num in range(total_pages):
            self.log(f"Processing page {page_num + 1}/{total_pages}")
            page = doc[page_num]
            
            # Get page dimensions
            page_rect = page.rect
            page_width = int(page_rect.width)
            page_height = int(page_rect.height)
            
            # Convert page to image for QR detection
            mat = fitz.Matrix(2, 2)  # 2x zoom
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Detect QR codes
            qr_codes = self.detect_qr_codes(img_data)
            
            # Resize design to fit page
            design_resized = design.resize((page_width, page_height), Image.Resampling.LANCZOS)
            
            # Create a copy for this page
            page_design = design_resized.copy()
            
            if qr_codes:
                self.log(f"Found {len(qr_codes)} QR codes on page {page_num + 1}")
                
                # Create alpha channel for QR protection
                alpha = Image.new('L', (page_width, page_height), int(255 * opacity))
                draw = ImageDraw.Draw(alpha)
                
                # Make QR areas transparent
                for qr in qr_codes:
                    # Scale coordinates back from zoomed image
                    x = int(qr['x'] / 2)
                    y = int(qr['y'] / 2)
                    w = int(qr['width'] / 2)
                    h = int(qr['height'] / 2)
                    
                    # Add padding
                    x1 = max(0, x - padding)
                    y1 = max(0, y - padding)
                    x2 = min(page_width, x + w + padding)
                    y2 = min(page_height, y + h + padding)
                    
                    # Draw transparent rectangle
                    draw.rectangle([x1, y1, x2, y2], fill=0)
                    self.log(f"Protected QR area: ({x1}, {y1}) to ({x2}, {y2})")
                
                # Apply alpha channel
                page_design.putalpha(alpha)
            else:
                self.log(f"No QR codes found on page {page_num + 1}")
                # Apply uniform opacity
                alpha = page_design.split()[-1]
                alpha = alpha.point(lambda p: int(p * opacity))
                page_design.putalpha(alpha)
            
            # Convert to bytes
            import io
            img_buffer = io.BytesIO()
            page_design.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Insert overlay
            page.insert_image(page_rect, stream=img_buffer.read(), overlay=True)
        
        # Save the modified PDF
        self.log(f"Saving to: {output_path}")
        doc.save(output_path)
        doc.close()
        
        self.log("Processing complete!")
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Overlay design on ticket PDFs while preserving QR codes'
    )
    parser.add_argument('-p', '--pdf', required=True, help='Input PDF file path')
    parser.add_argument('-d', '--design', required=True, help='Design image path (PNG/JPG)')
    parser.add_argument('-o', '--output', required=True, help='Output PDF file path')
    parser.add_argument('--opacity', type=float, default=0.7, 
                       help='Design opacity (0.0-1.0, default: 0.7)')
    parser.add_argument('--padding', type=int, default=15,
                       help='Padding around QR codes in pixels (default: 15)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.pdf):
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(1)
    
    if not os.path.exists(args.design):
        print(f"Error: Design file not found: {args.design}")
        sys.exit(1)
    
    if not 0 <= args.opacity <= 1:
        print("Error: Opacity must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process the PDF
    try:
        processor = SimpleTicketOverlay(verbose=args.verbose)
        success = processor.process_pdf(
            args.pdf,
            args.design,
            args.output,
            opacity=args.opacity,
            padding=args.padding
        )
        
        if success:
            print(f"✅ Success! Modified PDF saved to: {args.output}")
            
            # Print summary
            pdf_size = os.path.getsize(args.pdf) / 1024 / 1024
            output_size = os.path.getsize(args.output) / 1024 / 1024
            print(f"📊 Original size: {pdf_size:.2f} MB")
            print(f"📊 Output size: {output_size:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()