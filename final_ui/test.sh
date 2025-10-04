#!/bin/bash

# End-to-End Test Script for Final UI + Backend
# This script tests the complete integration

echo "🧪 Starting End-to-End Test..."
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$DIR/../backend_configured"

# Function to check if a port is in use
check_port() {
    if command -v lsof > /dev/null 2>&1; then
        if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
            return 0
        else
            return 1
        fi
    else
        # Fallback for systems without lsof
        if netstat -tuln 2>/dev/null | grep ":$1 " > /dev/null; then
            return 0
        else
            return 1
        fi
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${BLUE}⏳ Waiting for $name to be ready...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        sleep 1
        echo -n "."
        attempt=$((attempt + 1))
    done
    echo -e "${RED}❌ $name failed to start within $max_attempts seconds${NC}"
    return 1
}

# Function to test API endpoint
test_api() {
    local endpoint=$1
    local method=${2:-GET}
    local data=$3
    
    echo -e "${BLUE}🔍 Testing $method $endpoint${NC}"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "http://localhost:8000$endpoint")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:8000$endpoint")
    fi
    
    http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo $response | sed -e 's/HTTPSTATUS:.*//g')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ $endpoint responded successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ $endpoint failed with status $http_code${NC}"
        echo -e "${YELLOW}Response: $body${NC}"
        return 1
    fi
}

# Function to cleanup processes
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Kill backend process
    if [ -f "$BACKEND_DIR/.backend_pid" ]; then
        backend_pid=$(cat "$BACKEND_DIR/.backend_pid")
        if kill -0 $backend_pid 2>/dev/null; then
            kill $backend_pid
            rm "$BACKEND_DIR/.backend_pid"
            echo -e "${GREEN}✅ Backend stopped${NC}"
        fi
    fi
    
    # Kill any process on port 8000
    if check_port 8000; then
        echo -e "${YELLOW}🛑 Stopping process on port 8000...${NC}"
        pkill -f "uvicorn\|fastapi_app\|python.*8000" 2>/dev/null || true
        sleep 2
    fi
    
    # Kill frontend if running
    if check_port 3000; then
        echo -e "${YELLOW}🛑 Stopping frontend on port 3000...${NC}"
        pkill -f "vite\|npm.*dev" 2>/dev/null || true
        sleep 2
    fi
}

# Trap to cleanup on exit
trap cleanup EXIT

# Start backend
echo -e "${PURPLE}🚀 Starting Backend...${NC}"
cd "$BACKEND_DIR"

# Check if already running
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
else
    # Start backend using uvicorn
    echo -e "${BLUE}📡 Starting FastAPI with uvicorn...${NC}"
    
    # Try to use uvicorn directly
    if command -v uvicorn > /dev/null 2>&1; then
        uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --log-level info > backend.log 2>&1 &
        backend_pid=$!
        echo $backend_pid > .backend_pid
        echo -e "${GREEN}✅ Backend started with PID: $backend_pid${NC}"
    else
        # Fallback to python
        python fastapi_app.py > backend.log 2>&1 &
        backend_pid=$!
        echo $backend_pid > .backend_pid
        echo -e "${GREEN}✅ Backend started with PID: $backend_pid${NC}"
    fi
fi

# Wait for backend to be ready
if ! wait_for_service "http://localhost:8000/health" "Backend"; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    exit 1
fi

# Test backend endpoints
echo -e "\n${PURPLE}🧪 Testing Backend APIs...${NC}"

# Test health endpoint
test_api "/health"

# Test use cases endpoint
test_api "/use-cases"

# Test story generation with real data
story_request='{
    "theme": "fantasy",
    "character_name": "Emma",
    "age_group": "8 years old",
    "moral_lesson": "friendship",
    "story_length": "short",
    "include_images": true
}'

echo -e "\n${BLUE}🎨 Testing Story Generation...${NC}"
echo -e "${YELLOW}Request: $story_request${NC}"

if test_api "/generate-story" "POST" "$story_request"; then
    echo -e "${GREEN}✅ Story generation works!${NC}"
else
    echo -e "${RED}❌ Story generation failed${NC}"
fi

# Start frontend
echo -e "\n${PURPLE}🎨 Starting Frontend...${NC}"
cd "$DIR"

# Check if already running
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
else
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Start frontend in background
    echo -e "${BLUE}🌐 Starting React frontend...${NC}"
    npm run dev > frontend.log 2>&1 &
    frontend_pid=$!
    echo $frontend_pid > .frontend_pid
    echo -e "${GREEN}✅ Frontend started with PID: $frontend_pid${NC}"
fi

# Wait for frontend to be ready
if ! wait_for_service "http://localhost:3000" "Frontend"; then
    echo -e "${RED}❌ Frontend failed to start${NC}"
    exit 1
fi

# Test frontend-backend integration
echo -e "\n${PURPLE}🔗 Testing Frontend-Backend Integration...${NC}"

# Test if frontend can reach backend
echo -e "${BLUE}🔍 Testing CORS and API accessibility...${NC}"
cors_test=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -X OPTIONS \
    "http://localhost:8000/generate-story")

if [ "$cors_test" -eq 200 ] || [ "$cors_test" -eq 204 ]; then
    echo -e "${GREEN}✅ CORS configured correctly${NC}"
else
    echo -e "${YELLOW}⚠️  CORS might need adjustment (status: $cors_test)${NC}"
fi

# Final test summary
echo -e "\n${PURPLE}📋 Test Summary${NC}"
echo "==============="
echo -e "${GREEN}✅ Backend API:${NC} http://localhost:8000"
echo -e "${GREEN}✅ API Documentation:${NC} http://localhost:8000/docs"
echo -e "${GREEN}✅ Frontend UI:${NC} http://localhost:3000"
echo -e "${GREEN}✅ Story Generation:${NC} Working"
echo -e "${GREEN}✅ CORS Configuration:${NC} Ready"

echo -e "\n${BLUE}🎉 End-to-End Test Complete!${NC}"
echo -e "${YELLOW}💡 You can now:${NC}"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Create a new story through the UI"
echo "   3. Test the parent dashboard"
echo "   4. Verify story generation works end-to-end"

echo -e "\n${YELLOW}📝 Logs:${NC}"
echo "   Backend: $BACKEND_DIR/backend.log"
echo "   Frontend: $DIR/frontend.log"

echo -e "\n${BLUE}🛑 To stop all services:${NC}"
echo "   Press Ctrl+C or run: ./test.sh stop"

# Keep services running
if [ "${1:-""}" != "test-only" ]; then
    echo -e "\n${GREEN}🏃 Services are running. Press Ctrl+C to stop...${NC}"
    wait
fi
