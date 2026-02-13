#!/bin/bash
#############################################################################
#   SADRN - Stop Script
#   Stops all SADRN components cleanly
#############################################################################

SADRN_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SADRN_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "\n${CYAN}========== STOPPING SADRN ==========${NC}\n"

# Stop from PID files
for pidfile in .controller.pid .dashboard.pid .react.pid .mininet.pid; do
    if [ -f "$SADRN_DIR/$pidfile" ]; then
        PID=$(cat "$SADRN_DIR/$pidfile")
        if kill -0 $PID 2>/dev/null; then
            kill $PID 2>/dev/null
            echo -e "  ${GREEN}✓${NC} Stopped process $PID ($pidfile)"
        fi
        rm -f "$SADRN_DIR/$pidfile"
    fi
done

# Kill remaining processes
pkill -f "ryu.cmd.manager" 2>/dev/null && echo -e "  ${GREEN}✓${NC} Stopped Ryu controller" || true
pkill -f "react-dashboard/backend/app.py" 2>/dev/null && echo -e "  ${GREEN}✓${NC} Stopped dashboard backend" || true
pkill -f "dashboard/app.py" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null && echo -e "  ${GREEN}✓${NC} Stopped React frontend" || true
pkill -f "npm run dev" 2>/dev/null || true

# Free ports
fuser -k 3000/tcp 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 5001/tcp 2>/dev/null || true
fuser -k 6653/tcp 2>/dev/null || true

# Clean Mininet
echo -e "  ${CYAN}→${NC} Cleaning Mininet..."
sudo mn -c 2>/dev/null || true

echo -e "\n  ${GREEN}✓${NC} All SADRN components stopped\n"
