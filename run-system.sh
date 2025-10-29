#!/bin/bash

# Process Simulation Studio - Fixed Startup Script
echo "🚀 Starting Process Simulation Studio (FIXED VERSION)..."
echo "============================================="

# Kill any existing processes on these ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python 3 not found. Please install Python 3.8+ and try again."
    exit 1
fi

if ! command -v node >/dev/null 2>&1; then
    echo "❌ Node.js not found. Please install Node.js 16+ and try again."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Set up backend
echo ""
echo "🔧 Setting up backend..."
cd backend

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/updating Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set GROQ API KEY for LLM service
echo "🤖 Setting up LLM service with Groq API..."
export GROQ_API_KEY="Your API Key Here"

echo "🚀 Starting backend server..."
echo "Backend will be available at: http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Test backend
echo "🔍 Testing backend connection..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend is running successfully!"
else
    echo "❌ Backend failed to start. Check backend.log for errors."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Set up frontend  
echo ""
echo "🔧 Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
else
    echo "Node modules already installed, skipping..."
fi

echo "🚀 Starting frontend development server..."
echo "Frontend will be available at: http://localhost:3000"
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

echo ""
echo "🎉 Process Simulation Studio is now running!"
echo "============================================="
echo "✅ Backend:  http://localhost:8000 (API Docs: /docs)"
echo "✅ Frontend: http://localhost:3000"
echo ""
echo "📋 To test the system:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Try the sample prompts to modify the process"
echo "   3. Click 'Simulate' to see KPI impact"
echo ""
echo "📄 Logs:"
echo "   Backend: backend/backend.log"
echo "   Frontend: frontend/frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM
wait
