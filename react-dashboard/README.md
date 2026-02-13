# SADRN Dashboard

A real-time visualization dashboard for the Software-Defined Adaptive Disaster Response Network (SADRN) project. This dashboard provides an isolated simulation environment that mirrors the Mininet topology without requiring direct network connectivity.

## Features

### Network Topology Visualization
- **Wide, non-overlapping layout** with clear node positioning
- **6 OpenFlow switches**: 3 Core (S1-S3) + 3 Zone (S4-S6)
- **3 Dual-homed gateways**: GW-A, GW-B, GW-C with primary/backup uplinks
- **6 Disaster sensors**: Flood (water, rain), Earthquake (seismic, tilt), Fire (temperature, smoke)
- **Control Center Display**: Connected to all core switches
- **Animated packet routing** with visual path highlighting
- **Real-time route cost calculation** based on network conditions

### Interactive Controls
- **Click-to-adjust sensors**: Click any sensor node to reveal slider control
- **Sensor status thresholds**: NORMAL → WARNING → EMERGENCY
- **Switch failure simulation**: Click to fail/restore any switch
- **Link failure simulation**: Simulate link outages and observe rerouting
- **Intent-based routing**: Switch between balanced, low-latency, and high-priority modes

### Live Data Panels
- **Sensor Data Panel**: Real-time sensor readings sorted by priority
- **Route Info Panel**: Active routes with dynamic cost calculations
- **Packet Statistics**: Forwarded vs dropped packets tracking
- **Event Log**: Timestamped system events and alerts

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Topology   │  │  Controls   │  │   Event Log     │  │
│  │  Visualizer │  │   Panel     │  │                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ REST API + WebSocket
┌────────────────────────┴────────────────────────────────┐
│                   Flask Backend                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Topology   │  │   Dijkstra  │  │  Packet Stats   │  │
│  │   State     │  │   Routing   │  │   Tracking      │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Topology (Matches topology.py)

```
                    ┌─────────┐
                    │ DISPLAY │
                    │10.0.0.100│
                    └────┬────┘
           ┌─────────────┼─────────────┐
           │             │             │
      ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
      │   S1    │───│   S2    │───│   S3    │  (Core Mesh)
      │  Core   │   │  Core   │   │  Core   │
      └────┬────┘   └────┬────┘   └────┬────┘
           │             │             │
      ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
      │   S4    │   │   S5    │   │   S6    │  (Zone Switches)
      │ Zone A  │   │ Zone B  │   │ Zone C  │
      └────┬────┘   └────┬────┘   └────┬────┘
           │             │             │
      ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
      │  GW-A   │   │  GW-B   │   │  GW-C   │  (Gateways)
      │10.0.0.1 │   │10.0.0.2 │   │10.0.0.3 │
      └────┬────┘   └────┬────┘   └────┬────┘
       ┌───┴───┐     ┌───┴───┐     ┌───┴───┐
    Water  Rain  Seismic Tilt   Temp  Smoke   (Sensors)
```

### Gateway Dual-Homing
- **GW-A**: Primary → S4, Backup → S5
- **GW-B**: Primary → S5, Backup → S6  
- **GW-C**: Primary → S6, Backup → S4

## Quick Start

```bash
cd react-dashboard
./start.sh
```

This starts:
- **Backend**: Flask API on port 5000
- **Frontend**: Vite dev server on port 3000

Access the dashboard at: http://localhost:3000

## Manual Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/topology` | GET | Get full topology state |
| `/api/sensors` | GET | Get all sensors |
| `/api/sensors/<id>` | PUT | Update sensor value |
| `/api/switches/<id>/fail` | POST | Simulate switch failure |
| `/api/switches/<id>/restore` | POST | Restore failed switch |
| `/api/links/<id>/fail` | POST | Simulate link failure |
| `/api/links/<id>/restore` | POST | Restore failed link |
| `/api/intent` | GET/PUT | Get or set routing intent |
| `/api/routes` | GET | Get computed routes |
| `/api/packet_stats` | GET | Get packet statistics |
| `/api/reset` | POST | Reset simulation |

## Route Cost Calculation

Costs are dynamically calculated based on:
- **Base latency**: Core links (2ms), Zone links (5ms)
- **Intent modifiers**: 
  - Low latency: 0.5x base weight
  - High priority: 0.3x base weight
  - Low power: Battery levels considered
- **Congestion**: +0.5 per active route using link
- **Priority**: Emergency reduces gateway hop cost

## Technologies

- **Frontend**: React 18, Vite, TailwindCSS
- **Backend**: Flask, Flask-SocketIO, Flask-CORS
- **Communication**: REST API + WebSocket for real-time updates
- **Routing**: Dijkstra's algorithm with intent-based weights

## File Structure

```
react-dashboard/
├── start.sh              # Quick start script
├── README.md             # This file
├── backend/
│   ├── app.py            # Flask backend with routing logic
│   └── requirements.txt  # Python dependencies
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── App.jsx                # Main application
        ├── main.jsx               # Entry point
        ├── index.css              # Tailwind styles
        └── components/
            ├── TopologyVisualization.jsx  # Network topology SVG
            ├── ControllerPanel.jsx        # Intent & stats display
            ├── FailureControls.jsx        # Switch/link failure buttons
            ├── GatewayPanel.jsx           # Gateway status
            ├── Header.jsx                 # App header
            └── EventLog.jsx               # System event log
```

## Usage Tips

1. **Adjust Sensor Values**: Click on any sensor node in the topology to reveal a slider
2. **Simulate Failures**: Use the Failure Controls panel to fail switches or links
3. **Watch Rerouting**: When failures occur, observe route updates and cost changes
4. **Check Packet Stats**: The header shows sent/dropped packet counts
5. **View Routes**: Route info panel shows active paths with costs
6. **Reset**: Use the reset button in the header to restore initial state

## License

Part of the SADRN (Software-Defined Adaptive Disaster Response Network) project.
