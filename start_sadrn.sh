#!/bin/bash
#############################################################################
#   SADRN - Software-Defined Adaptive Disaster Response Network
#   Master Startup Script
#   
#   Usage:
#     Full System:      sudo bash start_sadrn.sh
#     Dashboard Only:   bash start_sadrn.sh --dashboard
#     Topology Only:    sudo bash start_sadrn.sh --topology
#     Status Check:     bash start_sadrn.sh --status
#     Stop All:         bash start_sadrn.sh --stop
#############################################################################

set -e

# Directory setup
SADRN_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SADRN_DIR"

# Get real user (non-root when running with sudo)
REAL_USER="${SUDO_USER:-$(whoami)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Output functions
banner() { echo -e "\n${CYAN}${BOLD}========== $1 ==========${NC}"; }
info() { echo -e "  ${CYAN}→${NC} $1"; }
ok() { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }

# Run command as real user (needed when running with sudo)
run_as_user() {
    if [ "$(id -u)" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        sudo -u "$REAL_USER" -H bash -c "$*"
    else
        bash -c "$*"
    fi
}

# Check if running as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        fail "This command requires root privileges. Use: sudo bash start_sadrn.sh"
        exit 1
    fi
}

#############################################################################
#   CLEANUP
#############################################################################
cleanup() {
    banner "CLEANUP"
    
    # Kill controller
    pkill -f "ryu.cmd.manager" 2>/dev/null && ok "Stopped Ryu controller" || true
    
    # Kill dashboard processes
    pkill -f "react-dashboard/backend/app.py" 2>/dev/null && ok "Stopped dashboard backend" || true
    pkill -f "dashboard/app.py" 2>/dev/null || true
    
    # Kill React/Vite
    pkill -f "node.*vite" 2>/dev/null && ok "Stopped React frontend" || true
    pkill -f "npm run dev" 2>/dev/null || true
    
    # Free ports
    fuser -k 3000/tcp 2>/dev/null || true
    fuser -k 5000/tcp 2>/dev/null || true
    fuser -k 5001/tcp 2>/dev/null || true
    fuser -k 6653/tcp 2>/dev/null || true
    
    # Clean Mininet
    mn -c 2>/dev/null && ok "Cleaned Mininet" || true
    
    # Remove PID files
    rm -f "$SADRN_DIR"/.*.pid 2>/dev/null || true
    
    # Clean old logs
    rm -f /tmp/gw_*.log /tmp/water_*.log /tmp/rain_*.log /tmp/seismic_*.log \
          /tmp/tilt_*.log /tmp/temp_*.log /tmp/smoke_*.log /tmp/display.log \
          /tmp/controller.log /tmp/dashboard*.log 2>/dev/null || true
    
    ok "Cleanup complete"
}

#############################################################################
#   START CONTROLLER
#############################################################################
start_controller() {
    banner "STARTING SDN CONTROLLER (port 6653)"
    
    cd "$SADRN_DIR/controller"
    python3 -m ryu.cmd.manager --ofp-tcp-listen-port 6653 sadrn_controller.py > /tmp/controller.log 2>&1 &
    local pid=$!
    echo "$pid" > "$SADRN_DIR/.controller.pid"
    sleep 3
    
    if kill -0 $pid 2>/dev/null; then
        ok "Ryu Controller running (PID $pid)"
        ok "OpenFlow listening on port 6653"
        ok "REST API at http://localhost:8080"
    else
        fail "Controller failed to start"
        cat /tmp/controller.log
        exit 1
    fi
    
    cd "$SADRN_DIR"
}

#############################################################################
#   START MININET TOPOLOGY
#############################################################################
start_topology() {
    banner "STARTING MININET TOPOLOGY"
    
    check_root
    cd "$SADRN_DIR"
    
    info "Creating 6-switch topology with 3 disaster zones..."
    info "This includes: 6 switches, 3 gateways, 6 sensors, 1 display server"
    echo ""
    
    # Run topology (this also starts all services)
    python3 "$SADRN_DIR/topology.py"
}

#############################################################################
#   START DASHBOARD BACKEND
#############################################################################
start_dashboard_backend() {
    banner "STARTING DASHBOARD BACKEND (port 5000)"
    
    cd "$SADRN_DIR/react-dashboard/backend"
    
    # Activate venv if exists, otherwise use system python
    if [ -d "venv" ]; then
        run_as_user "source venv/bin/activate && python3 app.py > /tmp/dashboard_backend.log 2>&1 &"
    else
        run_as_user "python3 app.py > /tmp/dashboard_backend.log 2>&1 &"
    fi
    
    sleep 2
    
    local pid=$(pgrep -f "react-dashboard/backend/app.py" | head -1)
    if [ -n "$pid" ]; then
        echo "$pid" > "$SADRN_DIR/.dashboard.pid"
        ok "Dashboard Backend running (PID $pid)"
        ok "API at http://localhost:5000"
    else
        warn "Dashboard backend may have issues - check /tmp/dashboard_backend.log"
    fi
    
    cd "$SADRN_DIR"
}

#############################################################################
#   START REACT FRONTEND
#############################################################################
start_react_frontend() {
    banner "STARTING REACT FRONTEND (port 3000)"
    
    cd "$SADRN_DIR/react-dashboard/frontend"
    
    # Install deps if needed
    if [ ! -d "node_modules" ]; then
        info "Installing npm dependencies..."
        run_as_user "npm install"
    fi
    
    run_as_user "npm run dev > /tmp/dashboard_frontend.log 2>&1 &"
    sleep 3
    
    local pid=$(pgrep -f "node.*vite" | head -1)
    if [ -n "$pid" ]; then
        echo "$pid" > "$SADRN_DIR/.react.pid"
        ok "React Frontend running (PID $pid)"
        ok "Dashboard at http://localhost:3000"
    else
        warn "React frontend may have issues - check /tmp/dashboard_frontend.log"
    fi
    
    cd "$SADRN_DIR"
}

#############################################################################
#   STATUS CHECK
#############################################################################
show_status() {
    banner "SADRN SYSTEM STATUS"
    
    echo ""
    echo -e "  ${BOLD}Services:${NC}"
    
    # Controller
    if pgrep -f "ryu.cmd.manager" > /dev/null 2>&1; then
        ok "SDN Controller    : http://localhost:8080 (running)"
    else
        fail "SDN Controller    : NOT running"
    fi
    
    # Dashboard Backend
    if curl -s -o /dev/null -w '' http://localhost:5000/api/health 2>/dev/null || \
       curl -s -o /dev/null -w '' http://localhost:5000/api/topology 2>/dev/null; then
        ok "Dashboard Backend : http://localhost:5000 (running)"
    else
        fail "Dashboard Backend : NOT running"
    fi
    
    # React Frontend
    if curl -s -o /dev/null -w '' http://localhost:3000 2>/dev/null; then
        ok "React Frontend    : http://localhost:3000 (running)"
    else
        fail "React Frontend    : NOT running"
    fi
    
    # Mininet/OVS
    local sw_count=$(ovs-vsctl list-br 2>/dev/null | wc -l)
    if [ "$sw_count" -ge 6 ]; then
        ok "OVS Switches      : $sw_count active"
    elif [ "$sw_count" -gt 0 ]; then
        warn "OVS Switches      : $sw_count active (expected 6)"
    else
        fail "OVS Switches      : NOT running"
    fi
    
    # Log files
    echo ""
    echo -e "  ${BOLD}Log Files:${NC}"
    for logfile in /tmp/controller.log /tmp/dashboard_backend.log /tmp/display.log; do
        if [ -f "$logfile" ]; then
            local lines=$(wc -l < "$logfile")
            ok "$logfile ($lines lines)"
        fi
    done
    
    echo ""
}

#############################################################################
#   TRAP CLEANUP
#############################################################################
trap_cleanup() {
    echo ""
    banner "SHUTTING DOWN"
    pkill -f "ryu.cmd.manager" 2>/dev/null && ok "Stopped controller" || true
    pkill -f "react-dashboard/backend/app.py" 2>/dev/null && ok "Stopped dashboard backend" || true
    pkill -f "node.*vite" 2>/dev/null && ok "Stopped React frontend" || true
    mn -c 2>/dev/null || true
    ok "All services stopped"
}

#############################################################################
#   HELP
#############################################################################
show_help() {
    echo ""
    echo "SADRN - Software-Defined Adaptive Disaster Response Network"
    echo ""
    echo "Usage: sudo bash start_sadrn.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  (no option)     Start complete system (controller + dashboard + topology)"
    echo "  --dashboard     Start dashboard only (backend + frontend, no sudo needed)"
    echo "  --topology      Start Mininet topology only (requires sudo)"
    echo "  --controller    Start SDN controller only"
    echo "  --stop          Stop all SADRN processes"
    echo "  --status        Show status of all components"
    echo "  --help          Show this help message"
    echo ""
    echo "Components:"
    echo "  - SDN Controller    - Ryu OpenFlow controller (port 6653, REST 8080)"
    echo "  - Dashboard Backend - Flask API server (port 5000)"
    echo "  - React Frontend    - Vite dev server (port 3000)"
    echo "  - Mininet Topology  - 6-switch SDN network with sensors"
    echo ""
    echo "Quick Start:"
    echo "  1. Full system:    sudo bash start_sadrn.sh"
    echo "  2. Open browser:   http://localhost:3000"
    echo ""
}

#############################################################################
#   MAIN
#############################################################################
case "${1:-}" in
    --stop)
        cleanup
        ;;
    --status)
        show_status
        ;;
    --dashboard)
        cleanup
        start_dashboard_backend
        start_react_frontend
        echo ""
        banner "DASHBOARD READY"
        echo -e "  Open ${GREEN}http://localhost:3000${NC} in your browser"
        echo -e "  Press Ctrl+C to stop"
        echo ""
        trap trap_cleanup EXIT
        wait
        ;;
    --topology)
        check_root
        cleanup
        start_controller
        start_topology
        ;;
    --controller)
        cleanup
        start_controller
        echo ""
        ok "Controller ready. Now run: sudo bash start_sadrn.sh --topology"
        ;;
    --help|-h)
        show_help
        ;;
    *)
        check_root
        cleanup
        
        echo ""
        start_controller
        start_dashboard_backend
        start_react_frontend
        
        echo ""
        banner "SYSTEM READY"
        echo -e "  ${GREEN}Dashboard:${NC}   http://localhost:3000"
        echo -e "  ${GREEN}API:${NC}         http://localhost:5000/api/topology"
        echo -e "  ${GREEN}Controller:${NC}  http://localhost:8080"
        echo ""
        
        trap trap_cleanup EXIT
        start_topology
        ;;
esac
