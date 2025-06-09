#!/usr/bin/env python3
"""
Complete QR Box Extractor
Extracts complete QR code boxes including text above (status and ticket code).

Usage:
    python complete_qr_extractor.py -p tickets.pdf -d design.png -o output.pdf --qr-scale 1.5
"""

import argparse
import sys
import os
from pathlib import Path
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyzbar import pyzbar
import io


class CompleteQRExtractor:
    def __init__(self, verbose=False):
        self.verbose = verbose
        
    def log(self, message):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[INFO] {message}")
    
    def extract_complete_qr_boxes(self, page):
        """Extract complete QR code boxes including text above"""
        # Convert page to image for QR detection
        mat = fitz.Matrix(2, 2)  # 2x zoom for better detection
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # Convert to cv2 image
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect QR codes first
        qr_regions = []
        decoded = pyzbar.decode(gray)
        
        for qr in decoded:
            x, y, w, h = qr.rect
            # Scale back to original coordinates
            qr_regions.append({
                'qr_x': x // 2,
                'qr_y': y // 2,
                'qr_width': w // 2,
                'qr_height': h // 2,
                'data': qr.data.decode('utf-8') if qr.data else ''
            })
        
        # If no QR codes found, try with preprocessing
        if not qr_regions:
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            decoded = pyzbar.decode(binary)
            
            for qr in decoded:
                x, y, w, h = qr.rect
                qr_regions.append({
                    'qr_x': x // 2,
                    'qr_y': y // 2,
                    'qr_width': w // 2,
                    'qr_height': h // 2,
                    'data': qr.data.decode('utf-8') if qr.data else ''
                })
        
        # Now expand each QR region to include text above
        complete_boxes = []
        
        for qr in qr_regions:
            # Estimate text area above QR code
            # Typically text takes about 60-80 pixels above the QR code
            text_height = 80
            side_padding = 20
            bottom_padding = 10
            
            # Calculate complete box coordinates
            box_x = max(0, qr['qr_x'] - side_padding)
            box_y = max(0, qr['qr_y'] - text_height)
            box_width = qr['qr_width'] + (2 * side_padding)
            box_height = qr['qr_height'] + text_height + bottom_padding
            
            # Ensure we don't go beyond page boundaries
            page_rect = page.rect
            box_x = max(0, box_x)
            box_y = max(0, box_y)
            box_width = min(box_width, page_rect.width - box_x)
            box_height = min(box_height, page_rect.height - box_y)
            
            complete_boxes.append({
                'x': box_x,
                'y': box_y,
                'width': int(box_width),
                'height': int(box_height),
                'qr_data': qr['data'],
                'image': None
            })
            
            self.log(f"QR box expanded from ({qr['qr_x']}, {qr['qr_y']}) "
                    f"to ({box_x}, {box_y}) size: {box_width}x{box_height}")
        
        # Extract the complete box images
        for box in complete_boxes:
            # Define clip rectangle for the complete box
            clip = fitz.Rect(
                box['x'],
                box['y'],
                box['x'] + box['width'],
                box['y'] + box['height']
            )
            
            # Get high-resolution image of the complete box
            pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(2, 2))
            box['image'] = pix.tobytes("png")
            
        return complete_boxes
    
    def mask_awaiting_payment(self, img, ticket_number=None):
        """Mask out 'Awaiting Payment' text and add ticket number"""
        # Convert to numpy array for processing
        img_array = np.array(img)
        height, width = img_array.shape[:2]
        
        # Create PIL image for drawing
        img_pil = Image.fromarray(img_array)
        draw = ImageDraw.Draw(img_pil)
        
        # Mask only the "Awaiting Payment" text area (typically in upper-middle portion)
        # This preserves the ticket code at the very top
        mask_y_start = int(height * 0.15)  # Start below ticket code
        mask_y_end = int(height * 0.30)    # End well before QR code area (reduced from 0.45)
        
        # Draw white rectangle only over "Awaiting Payment" area
        draw.rectangle([0, mask_y_start, width, mask_y_end], fill=(255, 255, 255))
        
        # Add ticket number if provided
        if ticket_number is not None:
            # Try to use a nice font with larger size for better clarity
            font_size = 36  # Increased from 24 for better visibility
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    try:
                        # Try common Linux fonts
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                    except:
                        # Use default font but try to make it larger
                        font = ImageFont.load_default()
            
            # Format ticket number with leading zeros
            text = f"{ticket_number:03d}"
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position in the white space we just created (centered)
            x = (width - text_width) // 2
            y = mask_y_start + ((mask_y_end - mask_y_start - text_height) // 2)
            
            # Draw the ticket number with improved clarity
            # Add a subtle outline for better contrast and clarity
            outline_color = (128, 128, 128)  # Light gray outline
            text_color = (0, 0, 0)  # Black text
            
            # Draw outline (offset by 1 pixel in each direction)
            for adj_x, adj_y in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((x + adj_x, y + adj_y), text, font=font, fill=outline_color)
            
            # Draw the main text
            draw.text((x, y), text, font=font, fill=text_color)
        
        return img_pil
    
    def process_pdf(self, pdf_path, design_path, output_path, qr_scale=1.0, qr_margin=20, 
                    qr_position='both', start_number=None, mask_awaiting=True):
        """Main processing function"""
        self.log(f"Opening PDF: {pdf_path}")
        doc = fitz.open(pdf_path)
        
        self.log(f"Loading design template: {design_path}")
        design = Image.open(design_path).convert('RGBA')
        design_width, design_height = design.size
        
        # Create new document for output
        output_doc = fitz.open()
        
        total_pages = len(doc)
        total_tickets = 0
        all_qr_boxes = []
        
        self.log(f"Processing {total_pages} pages")
        
        # First, collect all QR boxes
        for page_num in range(total_pages):
            self.log(f"Scanning page {page_num + 1}/{total_pages}")
            page = doc[page_num]
            qr_boxes = self.extract_complete_qr_boxes(page)
            all_qr_boxes.extend(qr_boxes)
            self.log(f"Found {len(qr_boxes)} complete QR boxes on page {page_num + 1}")
        
        self.log(f"Total QR boxes found: {len(all_qr_boxes)}")
        
        # Always create one ticket per QR code
        for box_idx, box in enumerate(all_qr_boxes):
            total_tickets += 1
            self.log(f"Creating ticket {total_tickets} for QR box {box_idx + 1}")
            
            # Create a new page with design dimensions
            new_page = output_doc.new_page(
                width=design_width,
                height=design_height
            )
            
            # Insert the design template
            design_buffer = io.BytesIO()
            design.save(design_buffer, format='PNG')
            design_buffer.seek(0)
            
            new_page.insert_image(
                new_page.rect,
                stream=design_buffer.read(),
                overlay=False
            )
            
            # Load and scale QR box image
            box_img = Image.open(io.BytesIO(box['image']))
            
            # Mask "Awaiting Payment" and add ticket number if requested
            if mask_awaiting or start_number is not None:
                ticket_num = start_number + total_tickets - 1 if start_number is not None else None
                box_img = self.mask_awaiting_payment(box_img, ticket_num)
            
            new_width = int(box_img.width * qr_scale)
            new_height = int(box_img.height * qr_scale)
            box_img = box_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Position QR codes based on qr_position setting
            positions_to_place = []
            
            if qr_position == 'left':
                positions_to_place.append('left')
            elif qr_position == 'right':
                positions_to_place.append('right')
            elif qr_position == 'both':
                positions_to_place.extend(['left', 'right'])
            
            # Place QR code(s) at specified position(s)
            for position in positions_to_place:
                if position == 'left':
                    box_x = qr_margin
                    box_y = design_height - new_height - qr_margin
                    position_name = "bottom-left"
                else:  # right
                    box_x = design_width - new_width - qr_margin
                    box_y = design_height - new_height - qr_margin
                    position_name = "bottom-right"
                
                # Ensure it fits
                if box_y < 0:
                    box_y = qr_margin
                if box_x < 0:
                    box_x = qr_margin
                
                # Save resized QR box
                box_buffer = io.BytesIO()
                box_img.save(box_buffer, format='PNG')
                box_buffer.seek(0)
                
                # Insert QR box
                box_rect = fitz.Rect(box_x, box_y, box_x + new_width, box_y + new_height)
                new_page.insert_image(box_rect, stream=box_buffer.read(), overlay=True)
                self.log(f"  Placed QR box at {position_name} ({box_x}, {box_y}) size: {new_width}x{new_height}")
            
            # Log ticket number if added
            if start_number is not None:
                self.log(f"  Added ticket number: {ticket_num:03d} in QR box")
        
        # Save the output document
        self.log(f"Saving {total_tickets} tickets to: {output_path}")
        output_doc.save(output_path)
        output_doc.close()
        doc.close()
        
        self.log("Processing complete!")
        return True, total_tickets


def main():
    parser = argparse.ArgumentParser(
        description='Generate tickets with complete QR boxes (including text above)'
    )
    parser.add_argument('-p', '--pdf', required=True, help='Input PDF file path containing QR codes')
    parser.add_argument('-d', '--design', required=True, help='Design template image (PNG/JPG)')
    parser.add_argument('-o', '--output', required=True, help='Output PDF file path')
    parser.add_argument('--qr-scale', type=float, default=1.0,
                       help='Scale factor for QR boxes (default: 1.0, try 0.8 for smaller)')
    parser.add_argument('--qr-margin', type=int, default=20,
                       help='Margin from edges for QR box placement in pixels (default: 20)')
    parser.add_argument('--qr-position', choices=['left', 'right', 'both'], default='both',
                       help='QR code placement: left (bottom-left), right (bottom-right), or both (default: both)')
    parser.add_argument('--start-number', type=int,
                       help='Starting ticket number (e.g., 1 for 001, 002, etc.)')
    parser.add_argument('--no-mask', action='store_true',
                       help='Do not mask "Awaiting Payment" text')
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
    
    if args.qr_scale <= 0:
        print("Error: QR scale must be positive")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process the PDF
    try:
        processor = CompleteQRExtractor(verbose=args.verbose)
        success, ticket_count = processor.process_pdf(
            args.pdf,
            args.design,
            args.output,
            qr_scale=args.qr_scale,
            qr_margin=args.qr_margin,
            qr_position=args.qr_position,
            start_number=args.start_number,
            mask_awaiting=not args.no_mask
        )
        
        if success:
            print(f"✅ Success! Modified PDF saved to: {args.output}")
            print(f"🎟️  Generated {ticket_count} tickets")
            if args.qr_position == 'both':
                print(f"📍 QR boxes placed at: bottom-left and bottom-right")
            elif args.qr_position == 'left':
                print(f"📍 QR boxes placed at: bottom-left")
            else:
                print(f"📍 QR boxes placed at: bottom-right")
            print(f"🔍 QR box scale: {args.qr_scale}x")
            print(f"📦 Includes: QR code + ticket code")
            if args.start_number:
                end_number = args.start_number + ticket_count - 1
                print(f"🔢 Ticket numbers: {args.start_number:03d} to {end_number:03d}")
            if not args.no_mask:
                print(f"✨ Masked 'Awaiting Payment' text")
            
            # Print summary
            output_size = os.path.getsize(args.output) / 1024 / 1024
            print(f"📊 Output size: {output_size:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()