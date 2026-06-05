#!/bin/bash

echo "=========================================="
echo "  THIWASCO SmartWater Platform"
echo "  Starting Application..."
echo "=========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8+"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r backend/Requirement.txt

# Start backend server
echo "🚀 Starting backend server..."
cd backend
python3 main.py &
BACKEND_PID=$!

# Wait for backend
sleep 2

# Open dashboard
echo ""
echo "=========================================="
echo "  ✅ Application Started!"
echo "=========================================="
echo ""
echo "  📡 Backend API: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo "  🌐 Dashboard: web/dashboard/index.html"
echo ""
echo "  👤 Test Users:"
echo "     Citizen: john@example.com / password123"
echo "     Technician: jane@thiwasco.co.ke / password123"
echo "     Admin: admin@thiwasco.co.ke / admin123"
echo ""
echo "  Press Ctrl+C to stop"
echo "=========================================="

# Open dashboard in browser
if command -v open &> /dev/null; then
    open web/dashboard/index.html
elif command -v xdg-open &> /dev/null; then
    xdg-open web/dashboard/index.html
fi

# Wait for backend process
wait $BACKEND_PID