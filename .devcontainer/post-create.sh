#!/bin/bash

echo "🚀 Setting up Ticket Manager development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install Flask flask-cors PyMuPDF opencv-python numpy Pillow pyzbar

# Create required directories
echo "📁 Creating required directories..."
mkdir -p uploads processed previews

# Install Node dependencies
echo "📦 Installing Node dependencies..."
npm install

# Create environment file for Astro
echo "🔧 Creating environment configuration..."
cat > .env.development << EOF
PUBLIC_API_URL=http://localhost:5000
EOF

# Start services in the background
echo "🎯 Starting development servers..."

# Create a simple process manager script
cat > start-servers.sh << 'EOF'
#!/bin/bash

# Function to handle Ctrl+C
trap 'kill $(jobs -p); exit' INT

# Start Flask server
echo "Starting Flask API server on port 5000..."
cd /workspace
python app.py &

# Wait a bit for Flask to start
sleep 3

# Start Astro dev server
echo "Starting Astro dev server on port 4321..."
cd /workspace
npm run dev -- --host &

# Keep the script running
wait
EOF

chmod +x start-servers.sh

echo "✅ Development environment setup complete!"
echo ""
echo "To start the servers, run: ./start-servers.sh"
echo "Or start them individually:"
echo "  - Flask API: python app.py"
echo "  - Astro Dev: npm run dev -- --host"
echo ""
echo "Access the application at:"
echo "  - Frontend: http://localhost:4321"
echo "  - Backend API: http://localhost:5000"