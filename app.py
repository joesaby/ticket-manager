# app.py - Flask Backend for Ticket Overlay Tool

import os
import io
import json
from pathlib import Path
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image, ImageDraw
from pyzbar import pyzbar
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import base64
import tempfile

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:4321", "http://localhost:3000"]}})  # Enable CORS for Astro dev server

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
PREVIEW_FOLDER = 'previews'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Create necessary directories
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, PREVIEW_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['PREVIEW_FOLDER'] = PREVIEW_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size


class TicketProcessor:
    """Main class for processing ticket PDFs and applying design overlays"""
    
    def __init__(self):
        self.qr_regions = []
        self.ticket_info = []
    
    def extract_pdf_info(self, pdf_path: str) -> Dict:
        """Extract ticket information and QR code locations from PDF"""
        doc = fitz.open(pdf_path)
        results = {
            'pages': [],
            'total_tickets': 0,
            'total_qr_codes': 0
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Convert page to image for QR detection
            mat = fitz.Matrix(2, 2)  # 2x zoom for better QR detection
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to numpy array for OpenCV
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Detect QR codes
            qr_codes = self._detect_qr_codes(img)
            
            # Get page dimensions
            page_rect = page.rect
            page_info = {
                'page_num': page_num,
                'width': page_rect.width,
                'height': page_rect.height,
                'qr_codes': []
            }
            
            # Process QR codes and map to PDF coordinates
            for qr in qr_codes:
                # Scale QR coordinates back to PDF coordinates
                x, y, w, h = qr['bbox']
                pdf_coords = {
                    'x': x / 2,  # Divide by zoom factor
                    'y': y / 2,
                    'width': w / 2,
                    'height': h / 2,
                    'data': qr['data']
                }
                page_info['qr_codes'].append(pdf_coords)
            
            # Extract text information (ticket details)
            text = page.get_text()
            ticket_info = self._parse_ticket_text(text)
            page_info['tickets'] = ticket_info
            
            results['pages'].append(page_info)
            results['total_tickets'] += len(ticket_info)
            results['total_qr_codes'] += len(qr_codes)
        
        doc.close()
        return results
    
    def _detect_qr_codes(self, image: np.ndarray) -> List[Dict]:
        """Detect QR codes in image using multiple methods"""
        qr_codes = []
        
        # Method 1: Direct detection
        try:
            decoded_objects = pyzbar.decode(image)
            for obj in decoded_objects:
                x, y, w, h = obj.rect
                qr_codes.append({
                    'bbox': (x, y, w, h),
                    'data': obj.data.decode('utf-8') if obj.data else ''
                })
        except Exception as e:
            print(f"Error in direct QR detection: {e}")
        
        # Method 2: Enhanced detection with preprocessing
        if not qr_codes:
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                # Apply threshold
                _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                decoded_objects = pyzbar.decode(thresh)
                
                for obj in decoded_objects:
                    x, y, w, h = obj.rect
                    qr_codes.append({
                        'bbox': (x, y, w, h),
                        'data': obj.data.decode('utf-8') if obj.data else ''
                    })
            except Exception as e:
                print(f"Error in enhanced QR detection: {e}")
        
        # Method 3: Contour-based detection as fallback
        if not qr_codes:
            qr_codes.extend(self._detect_qr_by_contours(image))
        
        return qr_codes
    
    def _detect_qr_by_contours(self, image: np.ndarray) -> List[Dict]:
        """Detect QR codes by finding square contours"""
        qr_regions = []
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Approximate contour to polygon
                approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                
                # Look for square-like shapes
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = w / float(h)
                    
                    # QR codes are typically square
                    if 0.8 < aspect_ratio < 1.2 and w > 50 and h > 50:
                        # Additional check for QR code patterns
                        roi = gray[y:y+h, x:x+w]
                        if self._is_likely_qr(roi):
                            qr_regions.append({
                                'bbox': (x, y, w, h),
                                'data': ''  # No data available with this method
                            })
        except Exception as e:
            print(f"Error in contour detection: {e}")
        
        return qr_regions
    
    def _is_likely_qr(self, roi: np.ndarray) -> bool:
        """Check if region likely contains QR code based on patterns"""
        try:
            # Simple heuristic: QR codes have high contrast patterns
            _, binary = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY)
            
            # Check for finder patterns (three corners of QR code)
            h, w = roi.shape
            corner_size = min(h, w) // 7
            
            # Sample corners
            corners = [
                binary[0:corner_size, 0:corner_size],  # Top-left
                binary[0:corner_size, w-corner_size:w],  # Top-right
                binary[h-corner_size:h, 0:corner_size]  # Bottom-left
            ]
            
            # Count transitions in each corner
            pattern_count = 0
            for corner in corners:
                transitions = np.sum(np.abs(np.diff(corner.flatten())) > 127)
                if transitions > 20:  # Arbitrary threshold
                    pattern_count += 1
            
            return pattern_count >= 2
        except:
            return False
    
    def _parse_ticket_text(self, text: str) -> List[Dict]:
        """Parse ticket information from extracted text"""
        tickets = []
        lines = text.split('\n')
        
        current_ticket = {}
        for i, line in enumerate(lines):
            line = line.strip()
            
            if 'Adult' in line and 'Age' in line:
                if current_ticket:
                    tickets.append(current_ticket)
                current_ticket = {'type': line}
            elif '@' in line and '.' in line:  # Email
                current_ticket['email'] = line
            elif '€' in line or '$' in line:  # Price
                current_ticket['price'] = line
            elif line.startswith('A-') and len(line) < 15:  # Ticket ID
                current_ticket['ticket_id'] = line
            elif 'Awaiting Payment' in line or 'Confirmed' in line:
                current_ticket['status'] = line
            elif any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']):
                current_ticket['date'] = line
        
        if current_ticket:
            tickets.append(current_ticket)
        
        return tickets
    
    def apply_overlay(self, pdf_path: str, design_path: str, output_path: str, 
                     opacity: float = 0.7, padding: int = 15) -> str:
        """Apply design overlay to PDF while preserving QR codes"""
        # Extract PDF information first
        pdf_info = self.extract_pdf_info(pdf_path)
        
        # Open PDF
        doc = fitz.open(pdf_path)
        
        # Load design image
        design = Image.open(design_path).convert('RGBA')
        
        for page_data in pdf_info['pages']:
            page_num = page_data['page_num']
            page = doc[page_num]
            
            # Get page dimensions
            page_rect = page.rect
            page_width = int(page_rect.width)
            page_height = int(page_rect.height)
            
            # Resize design to fit page
            design_resized = design.resize((page_width, page_height), Image.Resampling.LANCZOS)
            
            # Create a copy for this page
            page_design = design_resized.copy()
            
            if page_data['qr_codes']:
                # Create alpha channel for QR protection
                alpha = Image.new('L', (page_width, page_height), int(255 * opacity))
                draw = ImageDraw.Draw(alpha)
                
                # Make QR areas transparent
                for qr in page_data['qr_codes']:
                    x = int(qr['x'])
                    y = int(qr['y'])
                    w = int(qr['width'])
                    h = int(qr['height'])
                    
                    # Add padding around QR code
                    x1 = max(0, x - padding)
                    y1 = max(0, y - padding)
                    x2 = min(page_width, x + w + padding)
                    y2 = min(page_height, y + h + padding)
                    
                    # Draw transparent rectangle
                    draw.rectangle([x1, y1, x2, y2], fill=0)
                
                # Apply alpha channel
                page_design.putalpha(alpha)
            else:
                # Apply uniform opacity if no QR codes
                alpha = page_design.split()[-1]
                alpha = alpha.point(lambda p: int(p * opacity))
                page_design.putalpha(alpha)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            page_design.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Insert overlay
            page.insert_image(page_rect, stream=img_buffer.read(), overlay=True)
        
        # Save modified PDF
        doc.save(output_path)
        doc.close()
        
        return output_path


# Flask routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Ticket overlay service is running'}), 200


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and process overlay"""
    try:
        # Check for required files
        if 'pdf' not in request.files or 'design' not in request.files:
            return jsonify({'error': 'Both PDF and design files are required'}), 400
        
        pdf_file = request.files['pdf']
        design_file = request.files['design']
        
        # Validate file types
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Invalid PDF file'}), 400
        
        if not design_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return jsonify({'error': 'Invalid design file. Please upload PNG or JPG'}), 400
        
        # Save uploaded files
        pdf_filename = secure_filename(pdf_file.filename)
        design_filename = secure_filename(design_file.filename)
        
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        design_path = os.path.join(app.config['UPLOAD_FOLDER'], design_filename)
        
        pdf_file.save(pdf_path)
        design_file.save(design_path)
        
        # Get opacity from request
        opacity = float(request.form.get('opacity', 0.7))
        
        # Process files
        processor = TicketProcessor()
        
        # Extract PDF info for preview
        pdf_info = processor.extract_pdf_info(pdf_path)
        
        return jsonify({
            'success': True,
            'pdf_info': pdf_info,
            'pdf_filename': pdf_filename,
            'design_filename': design_filename
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process', methods=['POST'])
def process_overlay():
    """Process final overlay and return modified PDF"""
    try:
        data = request.json
        pdf_filename = data.get('pdf_filename')
        design_filename = data.get('design_filename')
        opacity = float(data.get('opacity', 0.7))
        padding = int(data.get('padding', 15))
        
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        design_path = os.path.join(app.config['UPLOAD_FOLDER'], design_filename)
        output_filename = f"modified_{pdf_filename}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        # Process overlay
        processor = TicketProcessor()
        processor.apply_overlay(pdf_path, design_path, output_path, opacity, padding)
        
        return send_file(output_path, as_attachment=True, 
                        download_name=output_filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)