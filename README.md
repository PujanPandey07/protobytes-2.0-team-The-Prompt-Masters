# SADRN — Software-Defined Adaptive Disaster Response Network

A real-time disaster monitoring system built on **Mininet** and **OpenFlow SDN**.
6 sensors across 3 disaster zones send data through gateways to a central
display, all visualised in a React dashboard.

---

## Architecture

```
                        ┌──────────┐
                        │ Display  │  10.0.0.100
                        │  Server  │  (UDP :9001)
                        └────┬─────┘
                             │
                     ┌───────┴───────┐
              ┌──────┤  S2 (Core-2)  ├──────┐
              │      └───────────────┘      │
        ┌─────┴─────┐                ┌──────┴────┐
        │ S1 (Core-1)├──────────────┤ S3 (Core-3)│
        └─────┬─────┘   core mesh   └──────┬─────┘
              │                             │
        ┌─────┴─────┐                ┌──────┴──────┐
        │ S4 (Flood) │               │ S6 (Fire)   │
        └──┬──┬──┬──┘                └──┬──┬──┬───┘
           │  │  │         ┌─────┐      │  │  │
     gw_a──┘  │  └──rain   │ S5  │  gw_c──┘  │  └──smoke
        water──┘     (EQ)   └┬─┬─┬┘     temp──┘
                        gw_b─┘ │ └─tilt
                        seismic┘

  Flood Zone (S4)       Earthquake Zone (S5)      Fire Zone (S6)
  ├─ gw_a   10.0.0.1    ├─ gw_b    10.0.0.2      ├─ gw_c    10.0.0.3
  ├─ water  10.0.0.11   ├─ seismic 10.0.0.21     ├─ temp    10.0.0.31
  └─ rain   10.0.0.12   └─ tilt    10.0.0.22     └─ smoke   10.0.0.32
```

**Data flow:** Sensor → Gateway (UDP :9000) → Display Server (UDP :9001)

---

## Project Structure

```
SADRN/
├── topo_working.py            # Main topology — run this
├── hosts/
│   ├── sensor.py              # 6 sensor types (flood, eq, fire)
│   └── gateway.py             # Gateway aggregation + forwarding
├── display/
│   └── display_server.py      # Central UDP display/alarm server
├── controller/
│   └── sadrn_controller.py    # Ryu SDN controller (optional)
├── dashboard/
│   └── app.py                 # Flask backend API (port 5001)
├── dashboard-react/           # React frontend (port 3000)
│   ├── src/
│   ├── vite.config.js
│   └── package.json
├── run_all.sh                 # ★ Master launch script
└── README.md                  # This file
```

---

## Prerequisites

| Software       | Version | Check Command        |
|----------------|---------|----------------------|
| Mininet        | >= 2.3  | `mn --version`       |
| Python         | >= 3.8  | `python3 --version`  |
| Open vSwitch   | >= 2.9  | `ovs-vsctl --version`|
| Node.js        | >= 16   | `node --version`     |
| npm            | >= 8    | `npm --version`      |

### Install Python dependencies

```bash
pip3 install flask flask-cors flask-socketio requests
```

### Install React dependencies

```bash
cd dashboard-react && npm install
```

---

## Quick Start (One Command)

```bash
cd ~/SADRN
sudo bash run_all.sh
```

This single command will:
1. Clean up any old processes
2. Start the **Dashboard Backend** (Flask API on port 5001)
3. Start the **React Frontend** (Vite dev server on port 3000)
4. Start the **Mininet 6-switch topology** with STP
5. Auto-start all **sensors, gateways, and display server**
6. Drop you into the Mininet CLI

When you `exit` the Mininet CLI, everything shuts down automatically.

---

## run_all.sh Options

| Command                  | What it does                            |
|--------------------------|-----------------------------------------|
| `sudo bash run_all.sh`  | Start everything (dashboard + Mininet)  |
| `bash run_all.sh --dash`| Dashboard only (no sudo needed)         |
| `sudo bash run_all.sh --topo` | Mininet only (no dashboard)        |
| `bash run_all.sh --stop`| Kill all SADRN processes                |
| `bash run_all.sh --status` | Show status of all components        |
| `bash run_all.sh --help`| Show usage help                         |

---

## Manual Start (Step by Step)

If you prefer to start each component individually:

### Step 1 — Start Dashboard Backend

```bash
cd ~/SADRN
python3 dashboard/app.py &
# Verify: curl http://localhost:5001/api/topology
```

### Step 2 — Start React Frontend

```bash
cd ~/SADRN/dashboard-react
npm run dev &
# Verify: curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Should print 200
```

### Step 3 — Start Mininet Topology

```bash
cd ~/SADRN
sudo python3 topo_working.py
```

This starts:
- 6 OVS switches (s1-s6) with STP enabled
- 3 gateways (gw_a, gw_b, gw_c)
- 6 sensors (water_a1, rain_a2, seismic_b1, tilt_b2, temp_c1, smoke_c2)
- 1 display server (display)
- All services auto-started

You will land at the `mininet>` prompt.

### Step 4 — Verify

```bash
mininet> pingall
# Expected: 0% dropped (90/90 received)
```

---

## Starting Individual Components from Mininet CLI

If services crash or you want to restart them manually:

### Restart Display Server
```bash
mininet> display pkill -f display_server
mininet> display python3 -u /home/mininet/SADRN/display/display_server.py 9001 > /tmp/display.log 2>&1 &
```

### Restart a Gateway
```bash
# Gateway A (flood zone)
mininet> gw_a pkill -f gateway
mininet> gw_a python3 /home/mininet/SADRN/hosts/gateway.py gw_a 10.0.0.100 \
    --listen-port 9000 --display-port 9001 > /tmp/gw_a.log 2>&1 &

# Gateway B (earthquake zone)
mininet> gw_b pkill -f gateway
mininet> gw_b python3 /home/mininet/SADRN/hosts/gateway.py gw_b 10.0.0.100 \
    --listen-port 9000 --display-port 9001 > /tmp/gw_b.log 2>&1 &

# Gateway C (fire zone)
mininet> gw_c pkill -f gateway
mininet> gw_c python3 /home/mininet/SADRN/hosts/gateway.py gw_c 10.0.0.100 \
    --listen-port 9000 --display-port 9001 > /tmp/gw_c.log 2>&1 &
```

### Restart a Sensor
```bash
# Flood sensors (send to gw_a = 10.0.0.1)
mininet> water_a1 python3 /home/mininet/SADRN/hosts/sensor.py flood_water \
    10.0.0.1 --port 9000 --interval 3 > /tmp/water_a1.log 2>&1 &

mininet> rain_a2 python3 /home/mininet/SADRN/hosts/sensor.py flood_rain \
    10.0.0.1 --port 9000 --interval 3 > /tmp/rain_a2.log 2>&1 &

# Earthquake sensors (send to gw_b = 10.0.0.2)
mininet> seismic_b1 python3 /home/mininet/SADRN/hosts/sensor.py eq_seismic \
    10.0.0.2 --port 9000 --interval 3 > /tmp/seismic_b1.log 2>&1 &

mininet> tilt_b2 python3 /home/mininet/SADRN/hosts/sensor.py eq_tilt \
    10.0.0.2 --port 9000 --interval 3 > /tmp/tilt_b2.log 2>&1 &

# Fire sensors (send to gw_c = 10.0.0.3)
mininet> temp_c1 python3 /home/mininet/SADRN/hosts/sensor.py fire_temp \
    10.0.0.3 --port 9000 --interval 3 > /tmp/temp_c1.log 2>&1 &

mininet> smoke_c2 python3 /home/mininet/SADRN/hosts/sensor.py fire_smoke \
    10.0.0.3 --port 9000 --interval 3 > /tmp/smoke_c2.log 2>&1 &
```

---

## Testing & Verification

### 1. Network Connectivity

```bash
mininet> pingall
# Expected: 0% dropped (90/90 received)

# Test specific paths
mininet> gw_a ping -c 3 10.0.0.100     # Flood gateway -> Display
mininet> water_a1 ping -c 3 10.0.0.1    # Sensor -> Its gateway
mininet> seismic_b1 ping -c 3 10.0.0.100 # Cross-zone: EQ sensor -> Display
```

### 2. Data Flow (Sensor -> Gateway -> Display)

```bash
# Watch display server receive data in real time
mininet> sh tail -f /tmp/display.log

# Expected output:
# [11:44:28] gw_a | flood_water  |   8.37 m       | emergency [ALARM]
# [11:44:28] gw_a | flood_rain   |  71.71 mm/h    | emergency [ALARM]
# [11:44:28] gw_b | eq_seismic   |   3.47 Richter | normal    [OK]
# [11:44:29] gw_b | eq_tilt      |  13.96 deg     | normal    [OK]
# [11:44:29] gw_c | fire_temp    |  85.88 C       | emergency [ALARM]
# [11:44:29] gw_c | fire_smoke   | 967.27 ppm     | emergency [ALARM]
```

### 3. Individual Service Logs

```bash
# Gateway logs (should show receive + forward)
mininet> sh tail -5 /tmp/gw_a.log
mininet> sh tail -5 /tmp/gw_b.log
mininet> sh tail -5 /tmp/gw_c.log

# Sensor logs
mininet> sh tail -5 /tmp/water_a1.log
mininet> sh tail -5 /tmp/seismic_b1.log
mininet> sh tail -5 /tmp/temp_c1.log
```

### 4. Dashboard API

```bash
mininet> sh curl -s http://localhost:5001/api/topology | python3 -m json.tool | head -20
mininet> sh curl -s http://localhost:5001/api/paths  | python3 -m json.tool | head -20
mininet> sh curl -s http://localhost:5001/api/battery
mininet> sh curl -s http://localhost:5001/api/emergency
```

### 5. React Dashboard

Open **http://localhost:3000** in a browser.

(If using a VM, forward port 3000 or use the VM's IP address.)

### 6. Switch Flow Tables

```bash
# Flows on each switch
mininet> sh ovs-ofctl dump-flows s1
mininet> sh ovs-ofctl dump-flows s4

# STP status
mininet> sh ovs-vsctl get bridge s1 stp_enable
# true

# All switch details
mininet> sh ovs-vsctl show
```

### 7. Log File Summary

```bash
mininet> sh wc -l /tmp/display.log /tmp/gw_a.log /tmp/gw_b.log /tmp/gw_c.log
```

---

## Network Details

### IP Address Map

| Host       | IP          | Role                 | Switch | Zone       |
|------------|-------------|----------------------|--------|------------|
| gw_a       | 10.0.0.1    | Gateway              | S4     | Flood      |
| gw_b       | 10.0.0.2    | Gateway              | S5     | Earthquake |
| gw_c       | 10.0.0.3    | Gateway              | S6     | Fire       |
| water_a1   | 10.0.0.11   | Water Level Sensor   | S4     | Flood      |
| rain_a2    | 10.0.0.12   | Rainfall Sensor      | S4     | Flood      |
| seismic_b1 | 10.0.0.21   | Seismograph          | S5     | Earthquake |
| tilt_b2    | 10.0.0.22   | Tilt Sensor          | S5     | Earthquake |
| temp_c1    | 10.0.0.31   | Temperature Sensor   | S6     | Fire       |
| smoke_c2   | 10.0.0.32   | Smoke Detector       | S6     | Fire       |
| display    | 10.0.0.100  | Display/Alarm Server | S2     | Central    |

### Switch Topology

| Switch | Role    | Connected To                              |
|--------|---------|-------------------------------------------|
| S1     | Core-1  | S2, S3 (mesh), S4 (flood zone)            |
| S2     | Core-2  | S1, S3 (mesh), S5 (EQ zone), Display      |
| S3     | Core-3  | S1, S2 (mesh), S6 (fire zone)             |
| S4     | Flood   | S1, gw_a, water_a1, rain_a2               |
| S5     | EQ      | S2, gw_b, seismic_b1, tilt_b2             |
| S6     | Fire    | S3, gw_c, temp_c1, smoke_c2               |

### Ports & Protocols

| Service            | Port | Protocol |
|--------------------|------|----------|
| Sensor -> Gateway  | 9000 | UDP      |
| Gateway -> Display | 9001 | UDP      |
| Dashboard Backend  | 5001 | HTTP     |
| React Frontend     | 3000 | HTTP     |
| OpenFlow Controller| 6653 | TCP      |

### Sensor Thresholds

| Sensor Type  | Range   | Alert Threshold | Unit    |
|--------------|---------|-----------------|---------|
| flood_water  | 0-10    | >= 7            | metres  |
| flood_rain   | 0-100   | >= 60           | mm/h    |
| eq_seismic   | 0-10    | >= 5            | Richter |
| eq_tilt      | 0-45    | >= 15           | degrees |
| fire_temp    | 0-100   | >= 55           | C       |
| fire_smoke   | 0-1000  | >= 300          | ppm     |

---

## Troubleshooting

### "X" in pingall (packet loss)

```bash
# STP may not have converged. Wait 15 seconds and retry:
mininet> pingall

# If still failing, check STP is enabled:
mininet> sh ovs-vsctl get bridge s1 stp_enable
# Should print: true
```

### Display server not receiving data

```bash
# Check if running
mininet> display ps aux | grep display_server

# Check log for errors
mininet> sh cat /tmp/display.log

# Restart
mininet> display pkill -f display_server
mininet> display python3 -u /home/mininet/SADRN/display/display_server.py 9001 \
    > /tmp/display.log 2>&1 &
```

### Gateway not forwarding

```bash
# Check log
mininet> sh tail -10 /tmp/gw_a.log

# Restart
mininet> gw_a pkill -f gateway
mininet> gw_a python3 /home/mininet/SADRN/hosts/gateway.py gw_a 10.0.0.100 \
    --listen-port 9000 --display-port 9001 > /tmp/gw_a.log 2>&1 &
```

### Dashboard not loading

```bash
# Check backend
curl http://localhost:5001/api/topology
# Should return JSON

# Check React
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Should return 200

# Restart
pkill -f "dashboard/app.py"
cd ~/SADRN && python3 dashboard/app.py &
pkill -f "npm run dev"
cd ~/SADRN/dashboard-react && npm run dev &
```

### Port already in use

```bash
sudo fuser -k 3000/tcp   # React
sudo fuser -k 5001/tcp   # Dashboard backend
```

### Full reset

```bash
sudo mn -c
pkill -f "dashboard/app.py"
killall node 2>/dev/null
sudo bash ~/SADRN/run_all.sh
```

---

## Stopping the System

From the Mininet CLI:
```bash
mininet> exit
```

The `run_all.sh` script automatically stops dashboard and React on exit.

Manual stop:
```bash
bash ~/SADRN/run_all.sh --stop
```

---

## File Reference

| File                           | Purpose                                                  |
|--------------------------------|----------------------------------------------------------|
| `topo_working.py`              | **Main topology** - 6 switches, STP, auto-starts services |
| `hosts/sensor.py`              | Sensor node - generates realistic data with drift/spikes |
| `hosts/gateway.py`             | Gateway node - receives sensors, forwards to display     |
| `display/display_server.py`    | Display server - UDP listener, prints data + alarms      |
| `dashboard/app.py`             | Flask API backend - topology/paths/battery/emergency     |
| `dashboard-react/`             | React frontend - visual network topology dashboard       |
| `controller/sadrn_controller.py` | Ryu SDN controller (optional, for advanced use)        |
| `run_all.sh`                   | **Master launch script** - starts everything             |
