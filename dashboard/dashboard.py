#!/usr/bin/env python3
"""
SADRN Dashboard Backend
Aggregates data from SDN Controller and provides REST API + Socket.IO for React dashboard
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import threading
import requests
import json
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration
CONTROLLER_URL = 'http://localhost:8080'

# State storage
state = {
    'topology': {'nodes': [], 'edges': []},
    'battery_levels': {'s1': 100, 's2': 100, 's3': 100},
    'emergency_status': {'h1': False, 'h2': False, 'h3': False},
    'disaster_types': {'h1': None, 'h2': None, 'h3': None},
    'paths': {},
    'recent_packets': [],
    'display_stats': {
        'total_packets': 0,
        'normal_packets': 0,
        'emergency_packets': 0,
        'packets_by_host': {'h1': 0, 'h2': 0, 'h3': 0},
        'avg_latency_ms': None
    },
    'controller_connected': False
}

state_lock = threading.Lock()


def fetch_controller_data():
    """Fetch data from SDN controller"""
    global state
    
    try:
        # Get topology from controller
        resp = requests.get(f'{CONTROLLER_URL}/sadrn/topology', timeout=2)
        if resp.ok:
            with state_lock:
                state['topology'] = resp.json()
                state['controller_connected'] = True
        
        # Get paths from controller
        resp = requests.get(f'{CONTROLLER_URL}/sadrn/paths', timeout=2)
        if resp.ok:
            with state_lock:
                state['paths'] = resp.json()
        
        # Get stats from controller
        resp = requests.get(f'{CONTROLLER_URL}/sadrn/stats', timeout=2)
        if resp.ok:
            data = resp.json()
            with state_lock:
                if 'battery_levels' in data:
                    for k, v in data['battery_levels'].items():
                        state['battery_levels'][f's{k}'] = v
                if 'emergency_status' in data:
                    state['emergency_status'].update(data['emergency_status'])
                state['display_stats']['total_packets'] = data.get('total', 0)
                state['display_stats']['normal_packets'] = data.get('normal', 0)
                state['display_stats']['emergency_packets'] = data.get('emergency', 0)
        
        # Get battery levels
        resp = requests.get(f'{CONTROLLER_URL}/sadrn/battery', timeout=2)
        if resp.ok:
            data = resp.json()
            with state_lock:
                for k, v in data.items():
                    state['battery_levels'][f's{k}'] = v
        
        # Get emergency status
        resp = requests.get(f'{CONTROLLER_URL}/sadrn/emergency', timeout=2)
        if resp.ok:
            data = resp.json()
            with state_lock:
                if 'status' in data:
                    state['emergency_status'].update(data['status'])
                if 'types' in data:
                    state['disaster_types'].update(data['types'])
                    
    except requests.exceptions.ConnectionError:
        with state_lock:
            state['controller_connected'] = False
    except Exception as e:
        pass


def poll_controller():
    """Background thread to poll controller and emit updates"""
    while True:
        fetch_controller_data()
        with state_lock:
            socketio.emit('live_update', {
                'display_stats': state['display_stats'],
                'recent_packets': state['recent_packets'],
                'paths': state['paths']
            })
        time.sleep(2)


# ============== API Routes ==============

@app.route('/api/state', methods=['GET'])
def get_state():
    """Get full state for React dashboard"""
    with state_lock:
        return jsonify({
            'topology': state['topology'],
            'battery_levels': state['battery_levels'],
            'emergency_status': state['emergency_status'],
            'disaster_types': state['disaster_types'],
            'paths': state['paths'],
            'recent_packets': state['recent_packets'][-50:],
            'display_stats': state['display_stats'],
            'controller_connected': state['controller_connected'],
            'timestamp': datetime.now().isoformat()
        })


@app.route('/api/topology', methods=['GET'])
def get_topology():
    """Get network topology"""
    with state_lock:
        return jsonify(state['topology'])


@app.route('/api/battery/<switch_id>', methods=['GET', 'POST'])
def handle_battery(switch_id):
    """Get or set battery level for a switch"""
    if request.method == 'POST':
        data = request.get_json() or {}
        level = data.get('level', 100)
        
        with state_lock:
            state['battery_levels'][switch_id] = level
        
        # Forward to SDN controller
        try:
            sw_num = switch_id.replace('s', '')
            requests.post(f'{CONTROLLER_URL}/sadrn/battery/{sw_num}',
                         json={'level': level}, timeout=2)
        except:
            pass
        
        socketio.emit('battery_update', {'switch': switch_id, 'level': level})
        return jsonify({'status': 'ok', 'switch': switch_id, 'level': level})
    else:
        with state_lock:
            return jsonify({'switch': switch_id, 'level': state['battery_levels'].get(switch_id, 100)})


@app.route('/api/emergency/<host>', methods=['GET', 'POST'])
def handle_emergency(host):
    """Get or set emergency status for a host"""
    if request.method == 'POST':
        data = request.get_json() or {}
        enabled = data.get('enabled', False)
        disaster_type = data.get('disaster_type')
        
        with state_lock:
            state['emergency_status'][host] = enabled
            state['disaster_types'][host] = disaster_type if enabled else None
        
        # Forward to SDN controller
        try:
            requests.post(f'{CONTROLLER_URL}/sadrn/emergency/{host}',
                         json={'status': enabled, 'disaster_type': disaster_type}, timeout=2)
        except:
            pass
        
        socketio.emit('emergency_update', {
            'host': host,
            'emergency': enabled,
            'disaster_type': disaster_type
        })
        return jsonify({'status': 'ok', 'host': host, 'emergency': enabled, 'disaster_type': disaster_type})
    else:
        with state_lock:
            return jsonify({
                'host': host,
                'emergency': state['emergency_status'].get(host, False),
                'disaster_type': state['disaster_types'].get(host)
            })


@app.route('/api/paths', methods=['GET'])
def get_paths():
    """Get current paths to display"""
    with state_lock:
        return jsonify(state['paths'])


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get packet statistics"""
    with state_lock:
        return jsonify(state['display_stats'])


@app.route('/api/packet', methods=['POST'])
def add_packet():
    """Receive packet data from display server"""
    data = request.get_json() or {}
    
    packet_info = {
        'source': data.get('source', 'unknown'),
        'destination': data.get('destination', 'unknown'),
        'priority': data.get('priority', 'normal'),
        'sensor_type': data.get('sensor_type', 'unknown'),
        'value': data.get('value'),
        'gateway': data.get('gateway'),
        'timestamp': datetime.now().isoformat()
    }
    
    with state_lock:
        state['recent_packets'].append(packet_info)
        state['recent_packets'] = state['recent_packets'][-100:]
        
        # Update stats
        state['display_stats']['total_packets'] += 1
        if data.get('priority') == 'emergency':
            state['display_stats']['emergency_packets'] += 1
        else:
            state['display_stats']['normal_packets'] += 1
        
        host = data.get('source', '').replace('10.0.0.', 'h')
        if host in state['display_stats']['packets_by_host']:
            state['display_stats']['packets_by_host'][host] += 1
    
    socketio.emit('live_update', {
        'display_stats': state['display_stats'],
        'recent_packets': state['recent_packets'][-50:]
    })
    
    return jsonify({'status': 'ok'})


# ============== Socket.IO Events ==============

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    with state_lock:
        emit('state_update', {
            'battery_levels': state['battery_levels'],
            'emergency_status': state['emergency_status'],
            'disaster_types': state['disaster_types']
        })


@socketio.on('request_state')
def handle_request_state():
    """Send current state to client"""
    with state_lock:
        emit('state_update', {
            'battery_levels': state['battery_levels'],
            'emergency_status': state['emergency_status'],
            'disaster_types': state['disaster_types']
        })


if __name__ == '__main__':
    print("=" * 60)
    print(" SADRN Dashboard Backend (with Socket.IO)")
    print("=" * 60)
    print(f" API Server:     http://localhost:5000")
    print(f" SDN Controller: {CONTROLLER_URL}")
    print("=" * 60)
    
    # Start background polling thread
    poll_thread = threading.Thread(target=poll_controller, daemon=True)
    poll_thread.start()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
