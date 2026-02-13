#!/bin/bash
echo "Starting SADRN Dashboard..."

# Start backend
cd /home/mininet/SADRN/react-dashboard/backend
python3 app.py &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 2

# Start frontend
cd /home/mininet/SADRN/react-dashboard/frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "============================================"
echo "  SADRN Dashboard is running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:5000"
echo "============================================"
echo "Press Ctrl+C to stop"

wait
