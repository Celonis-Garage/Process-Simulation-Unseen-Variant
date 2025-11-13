#!/bin/bash

# Process Simulation Studio - Fixed Startup Script
echo "🚀 Starting Process Simulation Studio (FIXED VERSION)..."
echo "============================================="

# Kill any existing processes on these ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:5175 | xargs kill -9 2>/dev/null || true

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

# Get absolute paths
BACKEND_DIR="$(pwd)"
VENV_PYTHON="$BACKEND_DIR/venv/bin/python"
VENV_PIP="$BACKEND_DIR/venv/bin/pip"
VENV_UVICORN="$BACKEND_DIR/venv/bin/uvicorn"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Installing/updating Python dependencies..."
$VENV_PIP install --upgrade pip
$VENV_PIP install -r requirements.txt

# Set GROQ API KEY for LLM service
echo "🤖 Setting up LLM service with Groq API..."
export GROQ_API_KEY="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"
#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 backup API key

# Check if ML model exists, train if needed
echo ""
echo "🤖 Checking ML model for KPI prediction..."
if [ ! -f "trained_models/kpi_prediction_model.keras" ]; then
    echo "⚠️  ML model not found in trained_models/"
    
    # Check if data files exist
    if [ -f "../data/order_kpis.csv" ] && [ -f "../data/users.csv" ] && [ -f "../data/items.csv" ]; then
        echo "✓ Data files found - training model..."
        echo "This will take 5-10 minutes depending on your CPU."
        echo "Training progress will be displayed below:"
        echo "─────────────────────────────────────────────────────"
        
        $VENV_PYTHON train_model.py
        
        if [ $? -eq 0 ]; then
            echo "─────────────────────────────────────────────────────"
            echo "✅ Model training completed successfully!"
        else
            echo "─────────────────────────────────────────────────────"
            echo "❌ Model training failed. Backend will use rule-based predictions."
            echo "   Check the error messages above for details."
            echo "   You can manually train by running: cd backend && python train_model.py"
        fi
    else
        echo "⚠️  Required data files not found in data/ directory"
        echo "   Missing files: users.csv, items.csv, suppliers.csv, order_kpis.csv"
        echo "   To enable ML predictions, run the Jupyter notebook (cells 41-45)"
        echo "   Backend will start with rule-based predictions only."
    fi
else
    echo "✅ ML model found - predictions enabled"
fi

echo ""
echo "🚀 Starting backend server..."
echo "Backend will be available at: http://localhost:8000"
$VENV_UVICORN main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
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

# Set up Omniverse 3D frontend
echo ""
echo "🎬 Setting up Omniverse 3D Visualization Frontend..."
cd ../omniverse-frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies for 3D frontend..."
    npm install
else
    echo "Node modules already installed, skipping..."
fi

echo "🚀 Starting Omniverse 3D frontend..."
echo "3D Visualization will be available at: http://localhost:5175"
npm run dev > omniverse-frontend.log 2>&1 &
OMNIVERSE_FRONTEND_PID=$!

# Wait for omniverse frontend to start
sleep 3

echo ""
echo "🎉 Process Simulation Studio is now running!"
echo "============================================="
echo "✅ Backend:             http://localhost:8000 (API Docs: /docs)"
echo "✅ Dashboard Frontend:  http://localhost:3000"
echo "✅ 3D Visualization:    http://localhost:5175"
echo ""
echo "📋 To test the system:"
echo "   1. Open http://localhost:3000 for the main dashboard"
echo "   2. Open http://localhost:5175 for 3D Omniverse visualization"
echo "   3. Try the sample prompts to modify the process"
echo "   4. Click 'Simulate' to see KPI impact"
echo ""
echo "📄 Logs:"
echo "   Backend:        backend/backend.log"
echo "   Frontend:       frontend/frontend.log"
echo "   3D Viewer:      omniverse-frontend/omniverse-frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    kill $OMNIVERSE_FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM
wait
