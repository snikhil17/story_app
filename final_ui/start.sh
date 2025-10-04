#!/bin/bash

# Startup script for the Final UI - Magic Wand AI Story Weaver

echo "🪄 Starting Magic Wand AI Story Weaver..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to start backend
start_backend() {
    echo -e "${PURPLE}🚀 Starting FastAPI Backend...${NC}"
    cd "$DIR/../backend_configured"
    
    # Check if backend is already running
    if check_port 8000; then
        echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
    else
        # Start backend in background
        python fastapi_app.py &
        BACKEND_PID=$!
        echo $BACKEND_PID > .backend_pid
        echo -e "${GREEN}✅ Backend started on port 8000 (PID: $BACKEND_PID)${NC}"
        
        # Wait for backend to be ready
        echo -e "${BLUE}⏳ Waiting for backend to be ready...${NC}"
        for i in {1..30}; do
            if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Backend is ready!${NC}"
                break
            fi
            sleep 1
            echo -n "."
        done
        echo
    fi
}

# Function to start frontend
start_frontend() {
    echo -e "${PURPLE}🎨 Starting React Frontend...${NC}"
    cd "$DIR"
    
    # Check if frontend is already running
    if check_port 3000; then
        echo -e "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
    else
        # Install dependencies if node_modules doesn't exist
        if [ ! -d "node_modules" ]; then
            echo -e "${BLUE}📦 Installing dependencies...${NC}"
            npm install
        fi
        
        # Start frontend
        echo -e "${GREEN}✅ Starting frontend on port 3000...${NC}"
        npm run dev
    fi
}

# Function to stop services
stop_services() {
    echo -e "${RED}🛑 Stopping services...${NC}"
    
    # Stop backend
    if [ -f "$DIR/../backend_configured/.backend_pid" ]; then
        BACKEND_PID=$(cat "$DIR/../backend_configured/.backend_pid")
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            rm "$DIR/../backend_configured/.backend_pid"
            echo -e "${GREEN}✅ Backend stopped${NC}"
        fi
    fi
    
    # Stop any process on port 3000 (frontend)
    if check_port 3000; then
        echo -e "${YELLOW}🛑 Stopping frontend...${NC}"
        # This will be handled by Ctrl+C
    fi
    
    exit 0
}

# Trap Ctrl+C to cleanup
trap stop_services INT

# Main execution
case ${1:-"dev"} in
    "dev")
        echo -e "${BLUE}🔧 Starting in development mode...${NC}"
        start_backend
        start_frontend
        ;;
    "backend")
        start_backend
        echo -e "${GREEN}✅ Backend only mode. Press Ctrl+C to stop.${NC}"
        wait
        ;;
    "frontend")
        start_frontend
        ;;
    "stop")
        stop_services
        ;;
    "help")
        echo -e "${BLUE}Usage:${NC}"
        echo "  ./start.sh [dev|backend|frontend|stop|help]"
        echo ""
        echo -e "${BLUE}Commands:${NC}"
        echo "  dev       - Start both backend and frontend (default)"
        echo "  backend   - Start only the FastAPI backend"
        echo "  frontend  - Start only the React frontend"
        echo "  stop      - Stop all services"
        echo "  help      - Show this help message"
        echo ""
        echo -e "${BLUE}URLs:${NC}"
        echo "  Frontend: http://localhost:3000"
        echo "  Backend:  http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use './start.sh help' for usage information"
        exit 1
        ;;
esac
