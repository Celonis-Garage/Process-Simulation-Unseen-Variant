#!/bin/bash

# Process Simulation Studio - Startup Script
# This script starts both the backend and frontend servers

echo "🚀 Starting Process Simulation Studio..."
echo "============================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 not found. Please install Python 3.8+ and try again."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js not found. Please install Node.js 16+ and try again."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm not found. Please install npm and try again."
    exit 1
fi

echo "✅ Prerequisites check passed!"
echo ""

# Backend setup and start
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set GROQ API KEY for LLM service
echo "Setting up LLM service..."
export GROQ_API_KEY="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"

echo "🚀 Starting backend server..."
echo "Backend will be available at: http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 3

# Frontend setup and start
echo ""
echo "🔧 Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

echo "🚀 Starting frontend development server..."
echo "Frontend will be available at: http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Process Simulation Studio is starting up!"
echo "============================================="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped. Goodbye!"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes to finish
wait
