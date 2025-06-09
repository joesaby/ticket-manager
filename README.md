# Ticket QR Extractor

A Python tool for extracting QR codes with text from ticket PDFs and creating customized tickets with design overlays.

## Overview

This tool extracts complete QR code boxes (including status text and ticket codes) from PDF tickets and places them on custom design templates. Perfect for creating branded tickets while preserving QR functionality.

## Features

- ✅ **Complete QR Box Extraction** - Captures QR codes with ticket codes
- ✅ **Automatic Text Masking** - Masks "Awaiting Payment" text with white
- ✅ **Ticket Numbering** - Automatically adds sequential ticket numbers
- ✅ **Custom Design Templates** - Use your own PNG/JPG designs as ticket backgrounds
- ✅ **Flexible Placement** - Dual QR mode (both corners) or single QR mode
- ✅ **Size Control** - Adjustable scaling for QR boxes
- ✅ **Batch Processing** - Process multiple tickets from multi-page PDFs
- ✅ **High Quality Output** - Maintains image quality with proper scaling

## Prerequisites

### System Requirements
- Python 3.9 or higher
- macOS, Linux, or Windows

### Required Python Libraries
```bash
pip install PyMuPDF opencv-python pillow pyzbar numpy
```

### System Dependencies

**For macOS:**
```bash
brew install zbar
```

**For Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y libzbar0
```

**For CentOS/RHEL:**
```bash
sudo yum install zbar
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ticket-manager
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies** (see above for your OS)

4. **Verify installation:**
   ```bash
   python3 complete_qr_extractor.py --help
   ```

## Usage

### Basic Usage (Both Corners)

Extract QR boxes and place them in both bottom corners:

```bash
python3 complete_qr_extractor.py -p input.pdf -d design.png -o output.pdf
```

### Single QR Mode (Left Corner Only)

Place QR box only in bottom-left corner:

```bash
python3 complete_qr_extractor.py -p input.pdf -d design.png -o output.pdf --qr-position left
```

### Single QR Mode (Right Corner Only)

Place QR box only in bottom-right corner:

```bash
python3 complete_qr_extractor.py -p input.pdf -d design.png -o output.pdf --qr-position right
```

### With Size Adjustment

Make QR boxes smaller (recommended 0.8 for complete boxes):

```bash
python3 complete_qr_extractor.py -p input.pdf -d design.png -o output.pdf --qr-scale 0.8
```

### With Ticket Numbering

Add sequential ticket numbers starting from 001:

```bash
python3 complete_qr_extractor.py -p input.pdf -d design.png -o output.pdf --start-number 1
```

### Full Example with All Options

```bash
python3 complete_qr_extractor.py \
  -p uploads/tickets.pdf \
  -d uploads/design.png \
  -o output/branded_tickets.pdf \
  --qr-scale 0.8 \
  --qr-margin 15 \
  -v
```

## Parameters

- `-p, --pdf` - Input PDF file containing QR codes (required)
- `-d, --design` - Design template image PNG/JPG (required)
- `-o, --output` - Output PDF file path (required)
- `--qr-scale` - Scale factor for QR boxes (default: 1.0)
  - Recommended: 0.8 for complete boxes with text
  - Range: 0.1 to 2.0
- `--qr-margin` - Margin from edges in pixels (default: 20)
- `--qr-position` - QR placement: `left`, `right`, or `both` (default: both)
- `--start-number` - Starting ticket number (e.g., 1 for 001, 2 for 002)
- `--no-mask` - Do not mask "Awaiting Payment" text (keep original)
- `-v, --verbose` - Enable detailed logging

## Input Requirements

### PDF Files
- **Format**: PDF with embedded QR codes
- **Layout**: Can contain multiple tickets per page
- **Text**: Should have status text and ticket codes above QR codes

### Design Templates
- **Format**: PNG or JPG
- **Resolution**: High resolution recommended (300+ DPI)
- **Size**: Should match desired output ticket dimensions

## Output

- **Format**: PDF with one ticket per page
- **QR Placement**: 
  - Both mode: Same QR code in bottom-left and bottom-right corners
  - Left mode: QR code in bottom-left corner only
  - Right mode: QR code in bottom-right corner only
- **Content**: Complete QR boxes including text

## Examples

### Example 1: Standard Dual QR Tickets with Numbering
```bash
python3 complete_qr_extractor.py \
  -p uploads/Offline-adult1.PDF \
  -d uploads/Screenshot.png \
  -o output/dual_tickets.pdf \
  --qr-scale 0.8 \
  --start-number 1 \
  -v
```

### Example 2: Single QR Tickets (Right Corner) without Masking
```bash
python3 complete_qr_extractor.py \
  -p uploads/Offline-adult1.PDF \
  -d uploads/Adult.png \
  -o output/single_tickets.pdf \
  --qr-position right \
  --qr-scale 0.6 \
  --qr-margin 25 \
  --no-mask \
  -v
```

### Example 3: Left Corner QR with Numbering
```bash
python3 complete_qr_extractor.py \
  -p uploads/tickets.pdf \
  -d uploads/design.png \
  -o output/left_tickets.pdf \
  --qr-position left \
  --qr-scale 0.8 \
  --start-number 1 \
  -v
```

### Example 4: Numbered Tickets Starting from 100 (Both Corners)
```bash
python3 complete_qr_extractor.py \
  -p uploads/tickets.pdf \
  -d uploads/design.png \
  -o output/numbered_tickets.pdf \
  --qr-position both \
  --qr-scale 0.8 \
  --start-number 100 \
  -v
```

## Tips and Best Practices

### QR Box Scaling
- **0.6 - 0.8**: Recommended for complete boxes (includes text)
- **0.8 - 1.0**: Standard size
- **1.0 - 1.5**: Larger boxes (ensure they fit)

### Design Templates
- Use consistent dimensions
- Leave space at bottom for QR placement
- High resolution for best quality

### Troubleshooting

**QR Codes Not Detected:**
- Ensure QR codes are clear and high contrast
- Check that text above QR codes is readable
- Try verbose mode (`-v`) to see detection details

**Boxes Too Large:**
- Reduce `--qr-scale` (try 0.6 or 0.7)
- Increase `--qr-margin` for more edge space

**Text Cut Off:**
- The tool automatically captures ~80 pixels above QR code
- Ensure source PDF has clear text layout

## File Structure

```
ticket-manager/
├── complete_qr_extractor.py    # Main script
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── CLAUDE.md                   # Technical documentation
├── uploads/                    # Sample input files
│   ├── Offline-adult1.PDF      # Sample ticket PDF
│   ├── Screenshot.png          # Sample design
│   └── Adult.png              # Alternative design
└── output/                     # Generated output files
```

## Technical Details

- **QR Detection**: Uses pyzbar with fallback preprocessing
- **Text Extraction**: Captures ~80 pixels above each QR code
- **Image Processing**: 2x resolution for accurate detection
- **PDF Generation**: One ticket per page output

## License

This project is open source. Check repository for license details.

## Support

For issues or questions, please refer to the repository documentation.