#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Ticket Manager Development Environment${NC}"
echo ""

# Check if running in devcontainer or locally
if [ -f /.dockerenv ]; then
    echo -e "${GREEN}Running in Docker container${NC}"
else
    echo -e "${GREEN}Running locally${NC}"
    
    # Check Python dependencies
    echo -e "${BLUE}Checking Python dependencies...${NC}"
    if ! python3 -c "import flask" 2>/dev/null; then
        echo -e "${RED}Python dependencies not installed. Installing...${NC}"
        pip install -r requirements.txt
    fi
    
    # Check Node dependencies
    echo -e "${BLUE}Checking Node dependencies...${NC}"
    if [ ! -d "node_modules" ]; then
        echo -e "${RED}Node dependencies not installed. Installing...${NC}"
        npm install
    fi
fi

# Create necessary directories
echo -e "${BLUE}Creating necessary directories...${NC}"
mkdir -p uploads processed previews

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup INT TERM

# Start Flask server
echo -e "${GREEN}Starting Flask API server on port 5000...${NC}"
python3 app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Start Astro dev server
echo -e "${GREEN}Starting Astro dev server on port 4321...${NC}"
npm run dev -- --host &
ASTRO_PID=$!

echo ""
echo -e "${GREEN}✅ Development servers started successfully!${NC}"
echo ""
echo -e "${BLUE}Access the application at:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:4321${NC}"
echo -e "  Backend API: ${GREEN}http://localhost:5000${NC}"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all servers${NC}"

# Wait for both processes
wait