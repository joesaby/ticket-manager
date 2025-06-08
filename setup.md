# Ticket Design Overlay Tool - Setup Guide

## Overview
This tool allows you to overlay custom designs on ticket PDFs while preserving QR codes and other critical information.

## Features
- 🎫 Automatic QR code detection and protection
- 🎨 Custom design overlay with adjustable opacity
- 👁️ Real-time preview before processing
- 📥 Download modified PDFs with preserved functionality
- 🔒 Safe processing - original QR codes remain scannable

## Installation

### 1. Python Requirements
Create a `requirements.txt` file:

```txt
Flask==2.3.3
flask-cors==4.0.0
PyMuPDF==1.23.8
opencv-python==4.8.1.78
numpy==1.24.3
Pillow==10.0.0
pyzbar==0.1.9
```

### 2. System Dependencies
Install system dependencies for QR code detection:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y libzbar0 libzbar-dev
```

**macOS:**
```bash
brew install zbar
```

**Windows:**
Download and install zbar from the official website.

### 3. Setup Steps

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir uploads processed

# Run the Flask backend
python app.py
```

## Usage

### Backend API Endpoints

1. **Upload Files**
   - Endpoint: `POST /upload`
   - Form data:
     - `pdf`: PDF file with tickets
     - `design`: Design image (PNG/JPG)
     - `opacity`: Opacity value (0-1)
   - Returns: Preview data and QR code locations

2. **Process Overlay**
   - Endpoint: `POST /process`
   - JSON body:
     ```json
     {
       "pdf_filename": "tickets.pdf",
       "design_filename": "design.png",
       "opacity": 0.7
     }
     ```
   - Returns: Modified PDF file

### Frontend Usage

1. Open the HTML file in a web browser
2. Upload your ticket PDF
3. Upload your design image
4. Adjust opacity slider
5. Preview the result
6. Download the modified PDF

## Advanced Features

### QR Code Detection Methods

The tool uses three methods to detect QR codes:

1. **Direct Detection**: Uses pyzbar library
2. **Enhanced Detection**: Preprocesses image with thresholding
3. **Contour Detection**: Finds square shapes that might be QR codes

### Customization Options

You can modify the `TicketProcessor` class to:

- Adjust QR code padding
- Change detection sensitivity
- Add support for other barcode types
- Implement batch processing

### Example Usage in Python

```python
from ticket_processor import TicketProcessor

# Initialize processor
processor = TicketProcessor()

# Extract PDF information
pdf_info = processor.extract_pdf_info('tickets.pdf')

# Apply overlay
processor.apply_overlay(
    pdf_path='tickets.pdf',
    design_path='my_design.png',
    output_path='modified_tickets.pdf',
    opacity=0.7,
    preserve_qr=True
)
```

## Troubleshooting

### Common Issues

1. **QR codes not detected**
   - Ensure PDF quality is high enough
   - Try adjusting the zoom factor in `extract_pdf_info`
   - Check if QR codes are actually embedded as images

2. **Design doesn't fit properly**
   - Design will be automatically resized to fit each page
   - Use high-resolution designs for best results
   - Consider the aspect ratio of your tickets

3. **Memory issues with large PDFs**
   - Process PDFs in batches
   - Reduce the zoom factor for QR detection
   - Implement page-by-page processing

### Performance Optimization

For large PDFs:
- Process pages in parallel using multiprocessing
- Cache QR detection results
- Use lower resolution for preview generation

## Security Considerations

- Validate all file uploads
- Implement rate limiting
- Sanitize filenames
- Add authentication for production use
- Clean up temporary files regularly

## Future Enhancements

1. **Batch Processing**: Handle multiple PDFs at once
2. **Template Library**: Save and reuse design templates
3. **Advanced Positioning**: Manual adjustment of design placement
4. **Multi-page Designs**: Different designs for different pages
5. **API Integration**: RESTful API for programmatic access

## License
This tool is provided as-is for personal and commercial use.