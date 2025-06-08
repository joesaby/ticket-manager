# Ticket Design Overlay Tool

A web application that allows users to overlay custom designs on ticket PDFs while preserving QR code functionality.

## Features

- 🎫 **QR Code Protection**: Automatically detects and preserves QR codes
- 🎨 **Custom Design Overlay**: Upload any PNG/JPG image as overlay
- 👁️ **Real-time Preview**: See how your tickets will look before processing
- ⚡ **Fast Processing**: Efficiently handles multi-page PDFs
- 🎯 **Precise Control**: Adjust opacity and QR padding

## Tech Stack

- **Frontend**: Astro + DaisyUI (Tailwind CSS)
- **Backend**: Python Flask
- **PDF Processing**: PyMuPDF
- **QR Detection**: pyzbar + OpenCV

## Quick Start

### Using Dev Container (Recommended)

1. Open project in VS Code
2. Install "Dev Containers" extension
3. Click "Reopen in Container" when prompted
4. Wait for container to build
5. Run `./start-servers.sh` in terminal

### Local Development

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

4. **Start development servers:**
   ```bash
   ./start-dev.sh
   ```

   Or start individually:
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
4. Adjust opacity and QR padding as needed
5. Preview the result
6. Download the modified PDF

## API Endpoints

- `GET /health` - Health check
- `POST /upload` - Upload PDF and design files
- `POST /process` - Process overlay and download result

## Project Structure

```
ticket-mgr/
├── src/                    # Astro frontend source
│   ├── components/         # Reusable components
│   ├── layouts/           # Page layouts
│   └── pages/             # Route pages
├── app.py                 # Flask backend
├── ticket-overlay.py      # CLI tool
├── .devcontainer/         # Dev container config
├── requirements.txt       # Python dependencies
└── package.json          # Node dependencies
```

## Environment Variables

- `PUBLIC_API_URL` - Backend API URL (default: http://localhost:5000)

## Troubleshooting

### QR codes not detected
- Ensure PDF has sufficient quality
- Try adjusting the detection parameters in `app.py`

### CORS errors
- Make sure both servers are running
- Check that API URL is correct in `.env.development`

### File upload fails
- Check file size limits
- Ensure correct file formats (PDF for tickets, PNG/JPG for design)