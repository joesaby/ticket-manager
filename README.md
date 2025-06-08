# Ticket Design Overlay Tool

A web application that allows users to overlay custom designs on ticket PDFs while preserving QR code functionality.

## Features

- 🎫 **QR Code Protection**: Automatically detects and preserves QR codes using multiple detection methods
- 🎨 **Custom Design Overlay**: Upload any PNG/JPG image as overlay with adjustable opacity
- 👁️ **Real-time Preview**: See how your tickets will look before processing
- ⚡ **Fast Processing**: Efficiently handles multi-page PDFs
- 🎯 **Precise Control**: Adjust opacity and QR padding for perfect results
- 📥 **Easy Download**: Get modified PDFs with preserved QR functionality
- 🔒 **Safe Processing**: Original QR codes remain scannable

## Tech Stack

- **Frontend**: Astro + DaisyUI (Tailwind CSS)
- **Backend**: Python Flask
- **PDF Processing**: PyMuPDF (fitz)
- **QR Detection**: pyzbar + OpenCV + PIL
- **Image Processing**: OpenCV, NumPy, Pillow

## Quick Start

### Using Development Script (Recommended)

```bash
./start-dev.sh
```

This will start both the Flask backend (port 5000) and Astro frontend (port 4321).

### Manual Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Install system dependencies:**
   - Ubuntu/Debian: `sudo apt-get install libzbar0 libzbar-dev`
   - macOS: `brew install zbar`
   - Windows: Download and install zbar from the official website

4. **Start servers individually:**
   ```bash
   # Terminal 1 - Flask API
   python app.py
   
   # Terminal 2 - Astro Frontend  
   npm run dev
   ```

## Usage

1. Access the application at http://localhost:4321
2. Upload your ticket PDF
3. Upload your design image (PNG/JPG)
4. Adjust opacity (0-100%) and QR padding as needed
5. Preview the result
6. Download the modified PDF

## API Endpoints

- `GET /health` - Health check
- `POST /upload` - Upload PDF and design files
  - Form data: `pdf` (file), `design` (file), `opacity` (float 0-1)
  - Returns: Preview data and QR code locations
- `POST /process` - Process overlay and download result
  - JSON body: `{"pdf_filename": "file.pdf", "design_filename": "design.png", "opacity": 0.7}`
  - Returns: Modified PDF file

## Project Structure

```
ticket-mgr/
├── src/                    # Astro frontend source
│   ├── components/         # Reusable components
│   │   ├── FileUpload.astro
│   │   └── Welcome.astro
│   ├── layouts/           # Page layouts
│   │   └── Layout.astro
│   ├── pages/             # Route pages
│   │   └── index.astro
│   └── assets/            # Static assets
├── app.py                 # Flask backend (main API)
├── standalone.py          # Simplified Flask backend
├── ticket-overlay.py      # CLI tool
├── uploads/               # Uploaded files directory
├── processed/             # Processed files directory
├── previews/              # Preview files directory
├── requirements.txt       # Python dependencies
├── package.json          # Node dependencies
└── start-dev.sh          # Development startup script
```

## Advanced Features

### QR Code Detection Methods

The tool uses three comprehensive methods to detect QR codes:

1. **Direct Detection**: Uses pyzbar library for standard QR detection
2. **Enhanced Detection**: Preprocesses images with thresholding and contrast enhancement
3. **Contour Detection**: Finds square shapes that might be QR codes as fallback

### Customization Options

You can modify the processing by adjusting:

- QR code padding (configurable buffer around detected codes)
- Detection sensitivity and parameters
- Opacity levels for design overlay
- Support for batch processing multiple PDFs

### Command Line Usage

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

## Environment Variables

- `PUBLIC_API_URL` - Backend API URL (default: http://localhost:5000)

## Troubleshooting

### QR codes not detected
- Ensure PDF has sufficient quality and resolution
- Try adjusting the zoom factor in `extract_pdf_info`
- Check if QR codes are embedded as images vs. vector graphics
- Verify the detection parameters in `app.py`

### Design doesn't fit properly
- Design images are automatically resized to fit each page
- Use high-resolution designs for best results
- Consider the aspect ratio of your tickets

### CORS errors
- Make sure both servers are running on correct ports
- Check that API URL is correct in environment variables
- Verify Flask CORS configuration

### File upload fails
- Check file size limits in Flask configuration
- Ensure correct file formats (PDF for tickets, PNG/JPG for design)
- Verify upload directory permissions

### Memory issues with large PDFs
- Process PDFs in smaller batches
- Reduce the zoom factor for QR detection
- Implement page-by-page processing for very large files

## Performance Optimization

For large PDFs:
- Process pages in parallel using multiprocessing
- Cache QR detection results between runs
- Use lower resolution for preview generation
- Implement progressive loading for large files

## Security Considerations

- All file uploads are validated for type and size
- Implement rate limiting for production use
- Sanitize all filenames and paths
- Add authentication for production deployment
- Regular cleanup of temporary files
- Input validation for all API endpoints

## Development

### Astro Commands

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |

### Python Development

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Flask development server
python app.py
```

## Future Enhancements

1. **Batch Processing**: Handle multiple PDFs simultaneously
2. **Template Library**: Save and reuse design templates
3. **Advanced Positioning**: Manual adjustment of design placement
4. **Multi-page Designs**: Different designs for different pages
5. **API Integration**: Full RESTful API for programmatic access
6. **Real-time Collaboration**: Multiple users working on designs
7. **Cloud Storage**: Integration with cloud storage services
8. **Mobile Support**: Responsive design for mobile devices

## License

This tool is provided as-is for personal and commercial use.

---

For more information about Astro, check [the documentation](https://docs.astro.build) or join the [Discord server](https://astro.build/chat).