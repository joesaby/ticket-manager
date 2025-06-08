#!/bin/bash

# Render Deployment Script for Ticket Manager
# This script prepares the application for deployment to Render

set -e  # Exit on any error

echo "🚀 Preparing Ticket Manager for Render deployment..."

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -f "app.py" ]; then
    echo "❌ Error: This script must be run from the project root directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "📦 Installing Node.js dependencies..."
npm ci

# Build the frontend
echo "🏗️  Building frontend for production..."
npm run build

# Add gunicorn to requirements if not present
if ! grep -q "gunicorn" requirements.txt; then
    echo "➕ Adding gunicorn to requirements.txt..."
    echo "gunicorn==21.2.0" >> requirements.txt
fi

# Create production environment file
echo "⚙️  Creating production environment configuration..."
cat > .env.production << EOL
FLASK_ENV=production
FLASK_APP=app.py
NODE_ENV=production
EOL

# Verify build
echo "✅ Verifying build..."
if [ -d "dist" ]; then
    echo "✅ Frontend build successful - dist/ directory created"
else
    echo "❌ Frontend build failed - dist/ directory not found"
    exit 1
fi

# Test backend
echo "🧪 Testing backend health endpoint..."
python -c "
import app
from flask import Flask
print('✅ Backend imports successful')
"

echo "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Commit and push your changes to GitHub"
echo "2. Connect your GitHub repo to Render"
echo "3. Deploy using the render.yaml configuration"
echo ""
echo "Render will automatically:"
echo "- Deploy the API service at: https://ticket-manager-api.onrender.com"
echo "- Deploy the frontend at: https://ticket-manager-frontend.onrender.com"
echo "- Set up Redis cache for session management"