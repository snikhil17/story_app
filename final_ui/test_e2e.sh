#!/bin/bash

# End-to-End Testing Script for Final UI with Real Backend
# This script tests the complete integration between frontend and backend

echo "🧪 Final UI End-to-End Testing Script"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_DIR="$DIR/../backend_configured"

# Test configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

# Function to log with timestamp
log() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')]${NC} $1"
}

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0

    log "${BLUE}⏳ Waiting for $name to be ready at $url...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            log "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done
    
    log "${RED}❌ $name failed to start after $max_attempts seconds${NC}"
    return 1
}

# Function to test API endpoint
test_api() {
    local endpoint=$1
    local description=$2
    local expected_status=${3:-200}
    
    log "${BLUE}🔍 Testing: $description${NC}"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$BACKEND_URL$endpoint")
    status_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$status_code" -eq "$expected_status" ]; then
        log "${GREEN}✅ $description - Status: $status_code${NC}"
        if [ ! -z "$body" ]; then
            echo "   Response: $(echo "$body" | jq -r . 2>/dev/null || echo "$body" | head -c 100)"
        fi
        return 0
    else
        log "${RED}❌ $description - Expected: $expected_status, Got: $status_code${NC}"
        echo "   Response: $body"
        return 1
    fi
}

# Function to test story generation
test_story_generation() {
    log "${PURPLE}🎭 Testing Real Story Generation${NC}"
    
    # Real story request payload
    story_request='{
        "theme": "fantasy",
        "character_name": "Emma",
        "age_group": "8 years old",
        "moral_lesson": "The importance of friendship and helping others",
        "story_length": "medium",
        "include_images": true
    }'
    
    log "${BLUE}📝 Sending story generation request...${NC}"
    echo "Request payload: $story_request"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -H "Content-Type: application/json" \
        -d "$story_request" \
        "$BACKEND_URL/generate-story")
    
    status_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$status_code" -eq "200" ]; then
        log "${GREEN}✅ Story generation successful!${NC}"
        
        # Parse and display story details
        title=$(echo "$body" | jq -r '.title' 2>/dev/null)
        content_length=$(echo "$body" | jq -r '.content | length' 2>/dev/null)
        chapters=$(echo "$body" | jq -r '.chapters | length' 2>/dev/null)
        
        echo "   📚 Title: $title"
        echo "   📝 Content length: $content_length characters"
        echo "   📖 Chapters: $chapters"
        
        # Save response for inspection
        echo "$body" | jq . > "/tmp/generated_story.json" 2>/dev/null
        log "${CYAN}💾 Full response saved to /tmp/generated_story.json${NC}"
        
        return 0
    else
        log "${RED}❌ Story generation failed - Status: $status_code${NC}"
        echo "   Response: $body"
        return 1
    fi
}

# Function to start backend
start_backend() {
    log "${PURPLE}🚀 Starting FastAPI Backend...${NC}"
    
    if check_port 8000; then
        log "${YELLOW}⚠️  Backend already running on port 8000${NC}"
        return 0
    fi
    
    cd "$BACKEND_DIR"
    
    # Check if required files exist
    if [ ! -f "fastapi_app.py" ]; then
        log "${RED}❌ fastapi_app.py not found in $BACKEND_DIR${NC}"
        return 1
    fi
    
    if [ ! -f "src/main.py" ]; then
        log "${RED}❌ src/main.py not found in $BACKEND_DIR${NC}"
        return 1
    fi
    
    # Start backend
    log "${BLUE}📦 Starting backend with real LLM agents...${NC}"
    python fastapi_app.py &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend_pid
    
    log "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    
    # Wait for backend to be ready
    if wait_for_service "$BACKEND_URL/health" "Backend"; then
        return 0
    else
        log "${RED}❌ Backend failed to start properly${NC}"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    log "${PURPLE}🎨 Starting React Frontend...${NC}"
    
    if check_port 3000; then
        log "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
        return 0
    fi
    
    cd "$DIR"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log "${BLUE}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Start frontend in background
    log "${BLUE}🏗️  Building and starting frontend...${NC}"
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > .frontend_pid
    
    log "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    
    # Wait for frontend to be ready
    if wait_for_service "$FRONTEND_URL" "Frontend"; then
        return 0
    else
        log "${RED}❌ Frontend failed to start properly${NC}"
        return 1
    fi
}

# Function to run comprehensive tests
run_tests() {
    log "${PURPLE}🧪 Running Comprehensive Backend Tests${NC}"
    
    local failed_tests=0
    
    # Basic API tests
    test_api "/" "Root endpoint" || ((failed_tests++))
    test_api "/health" "Health check" || ((failed_tests++))
    test_api "/use-cases" "Use cases listing" || ((failed_tests++))
    
    # Real story generation test
    test_story_generation || ((failed_tests++))
    
    if [ $failed_tests -eq 0 ]; then
        log "${GREEN}🎉 All tests passed! Backend is working correctly.${NC}"
        return 0
    else
        log "${RED}❌ $failed_tests test(s) failed.${NC}"
        return 1
    fi
}

# Function to show backend logs
show_backend_logs() {
    log "${BLUE}📋 Backend Configuration and Logs${NC}"
    
    if [ -f "$BACKEND_DIR/.backend_pid" ]; then
        BACKEND_PID=$(cat "$BACKEND_DIR/.backend_pid")
        if kill -0 $BACKEND_PID 2>/dev/null; then
            log "${GREEN}✅ Backend is running (PID: $BACKEND_PID)${NC}"
        else
            log "${RED}❌ Backend process not found${NC}"
        fi
    fi
    
    # Show use cases configuration
    if [ -f "$BACKEND_DIR/configs/use_cases.yaml" ]; then
        log "${CYAN}📋 Available Use Cases:${NC}"
        grep -A 5 "display_name\|description" "$BACKEND_DIR/configs/use_cases.yaml" | head -20
    fi
}

# Function to open browser
open_browser() {
    log "${PURPLE}🌐 Opening browser windows...${NC}"
    
    # Try different commands based on OS
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$FRONTEND_URL" >/dev/null 2>&1 &
        xdg-open "$BACKEND_URL/docs" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open "$FRONTEND_URL" >/dev/null 2>&1 &
        open "$BACKEND_URL/docs" >/dev/null 2>&1 &
    elif command -v start >/dev/null 2>&1; then
        start "$FRONTEND_URL" >/dev/null 2>&1 &
        start "$BACKEND_URL/docs" >/dev/null 2>&1 &
    else
        log "${YELLOW}⚠️  Could not auto-open browser. Please manually visit:${NC}"
        echo "   Frontend: $FRONTEND_URL"
        echo "   API Docs: $BACKEND_URL/docs"
    fi
}

# Function to cleanup
cleanup() {
    log "${RED}🛑 Cleaning up...${NC}"
    
    # Kill backend
    if [ -f "$BACKEND_DIR/.backend_pid" ]; then
        BACKEND_PID=$(cat "$BACKEND_DIR/.backend_pid")
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            rm "$BACKEND_DIR/.backend_pid"
            log "${GREEN}✅ Backend stopped${NC}"
        fi
    fi
    
    # Kill frontend
    if [ -f "$DIR/.frontend_pid" ]; then
        FRONTEND_PID=$(cat "$DIR/.frontend_pid")
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            rm "$DIR/.frontend_pid"
            log "${GREEN}✅ Frontend stopped${NC}"
        fi
    fi
    
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Main execution
case ${1:-"full"} in
    "full")
        log "${BLUE}🚀 Running full end-to-end test...${NC}"
        start_backend && \
        run_tests && \
        start_frontend && \
        show_backend_logs && \
        open_browser && \
        log "${GREEN}🎉 All services started successfully!${NC}" && \
        log "${CYAN}🌐 Visit $FRONTEND_URL to test the UI${NC}" && \
        log "${CYAN}📚 Visit $BACKEND_URL/docs for API documentation${NC}" && \
        log "${YELLOW}Press Ctrl+C to stop all services${NC}" && \
        wait
        ;;
    "backend")
        start_backend && run_tests && show_backend_logs
        log "${YELLOW}Press Ctrl+C to stop backend${NC}"
        wait
        ;;
    "test")
        run_tests
        ;;
    "story")
        test_story_generation
        ;;
    "logs")
        show_backend_logs
        ;;
    "stop")
        cleanup
        ;;
    "help")
        echo -e "${BLUE}Usage:${NC}"
        echo "  ./test_e2e.sh [full|backend|test|story|logs|stop|help]"
        echo ""
        echo -e "${BLUE}Commands:${NC}"
        echo "  full     - Start both services and run all tests (default)"
        echo "  backend  - Start and test backend only"
        echo "  test     - Run API tests against running backend"
        echo "  story    - Test real story generation"
        echo "  logs     - Show backend configuration and status"
        echo "  stop     - Stop all services"
        echo "  help     - Show this help"
        ;;
    *)
        log "${RED}❌ Unknown command: $1${NC}"
        echo "Use './test_e2e.sh help' for usage information"
        exit 1
        ;;
esac
