#!/usr/bin/env python3
"""
SADRN - Flask Backend API Server
Bridge between React Dashboard, Ryu Controller, and Mininet hosts
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests
import json
import socket
import threading
import time
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

RYU_URL = os.environ.get('RYU_CONTROLLER_URL', 'http://127.0.0.1:8080')
DISPLAY_URL = os.environ.get('DISPLAY_NODE_URL', 'http://10.0.0.100:8080')
CONTROL_PORTS = {'h1': ('10.0.0.1', 6001), 'h2': ('10.0.0.2', 6002), 'h3': ('10.0.0.3', 6003)}

state = {
    'battery_levels': {'s1': 100, 's2': 100, 's3': 100, 's4': 100, 's5': 100, 's6': 100},
    'emergency_status': {
        'water_a1': False, 'rain_a2': False,
        'seismic_b1': False, 'tilt_b2': False,
        'temp_c1': False, 'smoke_c2': False
    },
    'disaster_types': {
        'water_a1': None, 'rain_a2': None,
        'seismic_b1': None, 'tilt_b2': None,
        'temp_c1': None, 'smoke_c2': None
    },
    'connected_clients': 0,
    'simulation_running': False,
    'sensor_data': {}  # Store latest sensor readings
}


def get_mock_topology():
    """Return SADRN 6-switch topology with gateways, sensors, and display."""
    return {
        'nodes': [
            # Core switches (mesh)
            {'id': 's1', 'type': 'switch', 'label': 'Core-1', 'battery': state['battery_levels'].get('s1', 100)},
            {'id': 's2', 'type': 'switch', 'label': 'Core-2', 'battery': state['battery_levels'].get('s2', 100)},
            {'id': 's3', 'type': 'switch', 'label': 'Core-3', 'battery': state['battery_levels'].get('s3', 100)},
            # Zone switches
            {'id': 's4', 'type': 'switch', 'label': 'Flood-Zone', 'battery': state['battery_levels'].get('s4', 100)},
            {'id': 's5', 'type': 'switch', 'label': 'EQ-Zone', 'battery': state['battery_levels'].get('s5', 100)},
            {'id': 's6', 'type': 'switch', 'label': 'Fire-Zone', 'battery': state['battery_levels'].get('s6', 100)},
            # Gateways
            {'id': 'gw_a', 'type': 'gateway', 'ip': '10.0.0.1', 'zone': 'flood', 'switch': 's4'},
            {'id': 'gw_b', 'type': 'gateway', 'ip': '10.0.0.2', 'zone': 'earthquake', 'switch': 's5'},
            {'id': 'gw_c', 'type': 'gateway', 'ip': '10.0.0.3', 'zone': 'fire', 'switch': 's6'},
            # Flood sensors
            {'id': 'water_a1', 'type': 'sensor', 'sensor_type': 'flood_water', 'ip': '10.0.0.11', 'gateway': 'gw_a', 'switch': 's4'},
            {'id': 'rain_a2', 'type': 'sensor', 'sensor_type': 'flood_rain', 'ip': '10.0.0.12', 'gateway': 'gw_a', 'switch': 's4'},
            # Earthquake sensors
            {'id': 'seismic_b1', 'type': 'sensor', 'sensor_type': 'eq_seismic', 'ip': '10.0.0.21', 'gateway': 'gw_b', 'switch': 's5'},
            {'id': 'tilt_b2', 'type': 'sensor', 'sensor_type': 'eq_tilt', 'ip': '10.0.0.22', 'gateway': 'gw_b', 'switch': 's5'},
            # Fire sensors
            {'id': 'temp_c1', 'type': 'sensor', 'sensor_type': 'fire_temp', 'ip': '10.0.0.31', 'gateway': 'gw_c', 'switch': 's6'},
            {'id': 'smoke_c2', 'type': 'sensor', 'sensor_type': 'fire_smoke', 'ip': '10.0.0.32', 'gateway': 'gw_c', 'switch': 's6'},
            # Display server
            {'id': 'display', 'type': 'display', 'ip': '10.0.0.100', 'switch': 's2'},
        ],
        'edges': [
            # Core mesh (redundant paths)
            {'source': 's1', 'target': 's2', 'type': 'core-link'},
            {'source': 's2', 'target': 's3', 'type': 'core-link'},
            {'source': 's3', 'target': 's1', 'type': 'core-link'},
            # Zone switches to core
            {'source': 's4', 'target': 's1', 'type': 'zone-link'},
            {'source': 's5', 'target': 's2', 'type': 'zone-link'},
            {'source': 's6', 'target': 's3', 'type': 'zone-link'},
            # Display to core
            {'source': 'display', 'target': 's2', 'type': 'host-link'},
            # Gateways to zones
            {'source': 'gw_a', 'target': 's4', 'type': 'gateway-link'},
            {'source': 'gw_b', 'target': 's5', 'type': 'gateway-link'},
            {'source': 'gw_c', 'target': 's6', 'type': 'gateway-link'},
            # Flood sensors
            {'source': 'water_a1', 'target': 's4', 'type': 'sensor-link'},
            {'source': 'rain_a2', 'target': 's4', 'type': 'sensor-link'},
            # Earthquake sensors
            {'source': 'seismic_b1', 'target': 's5', 'type': 'sensor-link'},
            {'source': 'tilt_b2', 'target': 's5', 'type': 'sensor-link'},
            # Fire sensors
            {'source': 'temp_c1', 'target': 's6', 'type': 'sensor-link'},
            {'source': 'smoke_c2', 'target': 's6', 'type': 'sensor-link'},
        ]
    }


def get_mock_paths():
    """Return paths from sensors through gateways to display."""
    paths = {}
    # Sensor -> Gateway -> Display paths
    sensor_info = [
        ('water_a1', 'gw_a', 's4', 's1'),
        ('rain_a2', 'gw_a', 's4', 's1'),
        ('seismic_b1', 'gw_b', 's5', 's2'),
        ('tilt_b2', 'gw_b', 's5', 's2'),
        ('temp_c1', 'gw_c', 's6', 's3'),
        ('smoke_c2', 'gw_c', 's6', 's3'),
    ]
    
    for sensor, gateway, zone_sw, core_sw in sensor_info:
        # Normal path: sensor -> zone switch -> core switch -> display
        # Emergency path: may reroute through redundant core mesh
        is_emergency = state['emergency_status'].get(sensor, False)
        battery_low = state['battery_levels'].get(core_sw, 100) < 30
        
        if battery_low and core_sw == 's1':
            path = [zone_sw, 's2', 's3', 's1', 'display']  # Reroute via s2, s3
        elif battery_low and core_sw == 's2':
            path = [zone_sw, 's1', 's2', 'display']  # Reroute via s1
        elif battery_low and core_sw == 's3':
            path = [zone_sw, 's1', 's2', 's3', 'display']  # Long alternate
        else:
            path = [zone_sw, core_sw, 'display']  # Direct path
        
        paths[sensor] = {
            'path': path,
            'gateway': gateway,
            'emergency': is_emergency,
            'zone': zone_sw
        }
    
    return paths


@app.route('/api/topology', methods=['GET'])
def api_topology():
    try:
        return jsonify(requests.get(f'{RYU_URL}/sadrn/topology', timeout=5).json())
    except:
        return jsonify(get_mock_topology())


@app.route('/api/paths', methods=['GET'])
def api_paths():
    try:
        return jsonify(requests.get(f'{RYU_URL}/sadrn/paths', timeout=5).json())
    except:
        return jsonify(get_mock_paths())


@app.route('/api/battery/<switch_id>', methods=['POST'])
def api_set_battery(switch_id):
    level = max(1, min(100, request.json.get('level', 100)))
    state['battery_levels'][switch_id] = level
    try:
        requests.post(f'{RYU_URL}/sadrn/battery/{switch_id[1]}', json={'level': level}, timeout=2)
    except:
        pass
    socketio.emit('battery_update', {'switch': switch_id, 'level': level})
    return jsonify({'success': True, 'switch': switch_id, 'level': level})


@app.route('/api/battery', methods=['GET'])
def api_get_battery():
    return jsonify(state['battery_levels'])


@app.route('/api/emergency/<host_id>', methods=['POST'])
def api_set_emergency(host_id):
    data = request.json
    enabled, dtype = data.get('enabled', False), data.get('disaster_type')
    state['emergency_status'][host_id] = enabled
    state['disaster_types'][host_id] = dtype if enabled else None
    try:
        requests.post(f'{RYU_URL}/sadrn/emergency/{host_id}', json={'status': enabled, 'disaster_type': dtype}, timeout=2)
    except:
        pass
    socketio.emit('emergency_update', {'host': host_id, 'emergency': enabled, 'disaster_type': dtype})
    return jsonify({'success': True, 'host': host_id, 'emergency': enabled})


@app.route('/api/emergency', methods=['GET'])
def api_get_emergency():
    return jsonify({'status': state['emergency_status'], 'types': state['disaster_types']})


@app.route('/api/display/stats', methods=['GET'])
def api_display_stats():
    try:
        return jsonify(requests.get(f'{DISPLAY_URL}/stats', timeout=2).json())
    except:
        return jsonify({'total_packets': 0, 'normal_packets': 0, 'emergency_packets': 0})


@app.route('/api/display/packets', methods=['GET'])
def api_display_packets():
    try:
        return jsonify(requests.get(f'{DISPLAY_URL}/packets', timeout=2).json())
    except:
        return jsonify([])


@app.route('/api/state', methods=['GET'])
def api_state():
    topo = get_mock_topology()
    try:
        topo = requests.get(f'{RYU_URL}/sadrn/topology', timeout=2).json()
    except:
        pass
    return jsonify({
        'topology': topo, 'paths': get_mock_paths(), 'battery_levels': state['battery_levels'],
        'emergency_status': state['emergency_status'], 'disaster_types': state['disaster_types'],
        'simulation_running': state['simulation_running']
    })


@socketio.on('connect')
def on_connect():
    state['connected_clients'] += 1
    emit('state_update', {'battery_levels': state['battery_levels'], 'emergency_status': state['emergency_status'],
                          'disaster_types': state['disaster_types'], 'simulation_running': state['simulation_running']})


@socketio.on('disconnect')
def on_disconnect():
    state['connected_clients'] -= 1


@socketio.on('set_battery')
def ws_battery(data):
    switch_id = data.get('switch')
    level = data.get('level', 100)
    if switch_id in state['battery_levels']:
        state['battery_levels'][switch_id] = level
        try:
            requests.post(f'{RYU_URL}/sadrn/battery/{switch_id[1]}', json={'level': level}, timeout=1)
        except:
            pass
        socketio.emit('battery_update', {'switch': switch_id, 'level': level})


@socketio.on('trigger_disaster')
def ws_disaster(data):
    host_id = data.get('host')
    enabled = data.get('enabled', True)
    dtype = data.get('disaster_type')
    if host_id in state['emergency_status']:
        state['emergency_status'][host_id] = enabled
        state['disaster_types'][host_id] = dtype if enabled else None
        try:
            requests.post(f'{RYU_URL}/sadrn/emergency/{host_id}', json={'status': enabled, 'disaster_type': dtype}, timeout=1)
        except:
            pass
        socketio.emit('emergency_update', {'host': host_id, 'emergency': enabled, 'disaster_type': dtype})


def broadcaster():
    while True:
        time.sleep(2)
        if state['connected_clients'] > 0:
            try:
                stats, packets = {}, []
                try:
                    stats = requests.get(f'{DISPLAY_URL}/stats', timeout=1).json()
                    packets = requests.get(f'{DISPLAY_URL}/packets', timeout=1).json()
                except:
                    pass
                socketio.emit('live_update', {'display_stats': stats, 'recent_packets': packets[-10:], 'paths': get_mock_paths()})
            except:
                pass


threading.Thread(target=broadcaster, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5001))
    print(f"SADRN Dashboard API on port {port}")
    socketio.run(app, allow_unsafe_werkzeug=True, host='0.0.0.0', port=port, debug=False)
