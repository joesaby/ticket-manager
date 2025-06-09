# Ticket QR Extractor - Claude Documentation

## Project Overview
This project is a Python command-line tool for extracting complete QR code boxes (including text) from ticket PDFs and placing them on custom design templates. It provides a comprehensive solution for creating branded tickets while preserving QR code functionality and associated text information.

## Key Features
- **Complete QR Box Extraction**: Captures QR codes along with status text and ticket codes
- **Flexible Placement**: Supports both dual QR (both corners) and single QR modes
- **Design Integration**: Uses custom PNG/JPG templates as ticket backgrounds
- **Size Control**: Adjustable scaling for QR boxes
- **Batch Processing**: Handles multi-page PDFs efficiently
- **High Quality Output**: Maintains image resolution throughout processing

## Technical Architecture

### Core Script: `complete_qr_extractor.py`

The script implements a comprehensive ticket processing pipeline:

1. **QR Detection Phase**
   - Uses pyzbar library for primary QR code detection
   - Applies image preprocessing for difficult cases
   - 2x zoom factor for improved detection accuracy

2. **Box Extraction Phase**
   - Expands QR code boundaries to include text above (80px default)
   - Adds side padding (20px) and bottom padding (10px)
   - Captures complete ticket information area

3. **Design Integration Phase**
   - Loads custom design template
   - Scales QR boxes based on user parameters
   - Places boxes in specified positions (dual or single mode)

4. **Output Generation Phase**
   - Creates one ticket per page PDF
   - Maintains high resolution throughout
   - Preserves QR code scannability

### Key Classes and Methods

```python
class CompleteQRExtractor:
    def __init__(self, verbose=False)
    def extract_complete_qr_boxes(self, page)
    def detect_qr_codes(self, image_data)
    def process_pdf(self, pdf_path, design_path, output_path, ...)
    def apply_overlay(self, page, design, page_image_data, ...)
```

### Dependencies
- **PyMuPDF (fitz)**: PDF manipulation and rendering
- **OpenCV**: Image processing and enhancement
- **Pillow (PIL)**: Image scaling and format conversion
- **pyzbar**: QR code detection and decoding
- **NumPy**: Array operations for image processing

## Implementation Details

### QR Box Detection Algorithm
```
1. Convert PDF page to high-resolution image (2x zoom)
2. Detect QR codes using pyzbar
3. If no QR codes found:
   - Apply binary thresholding
   - Retry detection with preprocessed image
4. For each detected QR code:
   - Expand boundaries upward by 80px (text area)
   - Add 20px horizontal padding
   - Add 10px bottom padding
   - Ensure boundaries stay within page limits
```

### Placement Logic
**Dual QR Mode (Default):**
- Processes QR codes in pairs
- First QR: bottom-left corner
- Second QR: bottom-right corner
- Creates one ticket per pair

**Single QR Mode:**
- One QR box per ticket
- Placed in bottom-right corner
- Creates one ticket per QR code

### Scaling and Positioning
- QR boxes are scaled uniformly (width and height)
- Position calculation ensures boxes fit within design boundaries
- Automatic adjustment if scaled box exceeds margins

## Command-Line Interface

```bash
python3 complete_qr_extractor.py [OPTIONS]
```

### Required Parameters
- `-p, --pdf PATH` - Input PDF file containing tickets
- `-d, --design PATH` - Design template image (PNG/JPG)
- `-o, --output PATH` - Output PDF file path

### Optional Parameters
- `--qr-scale FLOAT` - Scale factor for QR boxes (default: 1.0)
- `--qr-margin INT` - Margin from edges in pixels (default: 20)
- `--single-qr` - Use single QR mode instead of dual
- `-v, --verbose` - Enable detailed logging

## Performance Characteristics

### Processing Speed
- Page conversion: ~0.5-1s per page (depends on resolution)
- QR detection: ~0.1-0.3s per QR code
- Output generation: ~0.2-0.5s per ticket

### Memory Usage
- Scales linearly with PDF page count
- Peak usage during high-resolution page rendering
- Efficient cleanup after each page processing

### Output Quality
- Maintains source QR code resolution
- High-quality image scaling algorithms
- No compression artifacts in final output

## Error Handling

### Detection Failures
- Falls back to preprocessing if initial detection fails
- Logs warnings for undetected QR codes
- Continues processing remaining pages

### Size Constraints
- Validates that scaled boxes fit within design
- Automatically adjusts position if needed
- Warns user if boxes are too large

### File Validation
- Checks file existence before processing
- Validates file types (PDF, PNG, JPG)
- Creates output directories if needed

## Best Practices

### Recommended Settings
```bash
# For standard tickets with text
--qr-scale 0.8 --qr-margin 15

# For compact designs
--qr-scale 0.6 --qr-margin 10

# For large format tickets
--qr-scale 1.2 --qr-margin 30
```

### Design Guidelines
1. **Template Size**: Match intended output dimensions
2. **Clear Space**: Leave bottom area clear for QR placement
3. **Resolution**: Use 300+ DPI for best quality
4. **Format**: PNG with transparency for overlays

### Input PDF Requirements
1. **QR Codes**: High contrast, properly formatted
2. **Text Layout**: Clear text above QR codes
3. **Page Structure**: Consistent ticket layout
4. **Resolution**: Higher resolution improves detection

## Troubleshooting Guide

### Common Issues

**Issue: QR codes not detected**
```
Solution:
1. Check QR code contrast and clarity
2. Ensure QR codes are standard format
3. Try verbose mode to see detection attempts
4. Verify PDF is not corrupted
```

**Issue: Text cut off in extraction**
```
Solution:
1. Default captures 80px above QR code
2. Modify text_height in extract_complete_qr_boxes() if needed
3. Ensure consistent text placement in source PDF
```

**Issue: Output boxes too large**
```
Solution:
1. Reduce --qr-scale (try 0.6-0.8)
2. Increase --qr-margin for more edge space
3. Use smaller design templates
```

## Future Enhancement Opportunities

1. **Configurable Text Area**: Allow custom text capture height
2. **Multiple Templates**: Support different designs per ticket type
3. **Text Recognition**: OCR integration for text extraction
4. **Batch Templates**: Apply different designs in one run
5. **Position Presets**: Named positioning configurations
6. **Preview Mode**: Generate preview before final processing
7. **API Integration**: REST API for web services
8. **Cloud Storage**: Direct upload/download from cloud

## Code Quality Considerations

### Modularity
- Clear separation of detection, extraction, and generation phases
- Reusable methods for common operations
- Easy to extend with new features

### Error Handling
- Comprehensive exception handling
- Informative error messages
- Graceful degradation on failures

### Performance
- Efficient image processing pipelines
- Memory-conscious implementation
- Scalable to large PDF files

This documentation provides the complete technical reference for the Ticket QR Extractor project.