"""SADRN Flask Backend - Matching topology.py architecture"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading, time, heapq, random
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 6 Switches matching topology.py
SWITCHES = {
    's1': {'id': 's1', 'name': 'Core Switch 1', 'type': 'core', 'status': 'active', 'battery': 100},
    's2': {'id': 's2', 'name': 'Core Switch 2', 'type': 'core', 'status': 'active', 'battery': 100},
    's3': {'id': 's3', 'name': 'Core Switch 3', 'type': 'core', 'status': 'active', 'battery': 100},
    's4': {'id': 's4', 'name': 'Zone A Switch', 'type': 'zone', 'status': 'active', 'battery': 100},
    's5': {'id': 's5', 'name': 'Zone B Switch', 'type': 'zone', 'status': 'active', 'battery': 100},
    's6': {'id': 's6', 'name': 'Zone C Switch', 'type': 'zone', 'status': 'active', 'battery': 100},
}

# Links matching topology.py
SWITCH_LINKS = [
    # Core mesh (s1-s2-s3 triangle)
    {'id': 'l1', 'source': 's1', 'target': 's2', 'status': 'active', 'latency': 2, 'bandwidth': 1000, 'type': 'core'},
    {'id': 'l2', 'source': 's2', 'target': 's3', 'status': 'active', 'latency': 2, 'bandwidth': 1000, 'type': 'core'},
    {'id': 'l3', 'source': 's3', 'target': 's1', 'status': 'active', 'latency': 2, 'bandwidth': 1000, 'type': 'core'},
    # Zone to core
    {'id': 'l4', 'source': 's4', 'target': 's1', 'status': 'active', 'latency': 5, 'bandwidth': 100, 'type': 'zone'},
    {'id': 'l5', 'source': 's5', 'target': 's2', 'status': 'active', 'latency': 5, 'bandwidth': 100, 'type': 'zone'},
    {'id': 'l6', 'source': 's6', 'target': 's3', 'status': 'active', 'latency': 5, 'bandwidth': 100, 'type': 'zone'},
]

# Gateways matching topology.py (dual-homed)
GATEWAYS = {
    'gw_a': {'id': 'gw_a', 'name': 'Gateway A (Flood)', 'ip': '10.0.0.1', 'status': 'active', 
             'primary_switch': 's4', 'backup_switch': 's5', 'active_uplink': 's4',
             'sensors': ['water_a1', 'rain_a2'], 'priority': 'NORMAL'},
    'gw_b': {'id': 'gw_b', 'name': 'Gateway B (Earthquake)', 'ip': '10.0.0.2', 'status': 'active',
             'primary_switch': 's5', 'backup_switch': 's6', 'active_uplink': 's5',
             'sensors': ['seismic_b1', 'tilt_b2'], 'priority': 'NORMAL'},
    'gw_c': {'id': 'gw_c', 'name': 'Gateway C (Fire)', 'ip': '10.0.0.3', 'status': 'active',
             'primary_switch': 's6', 'backup_switch': 's4', 'active_uplink': 's6',
             'sensors': ['temp_c1', 'smoke_c2'], 'priority': 'NORMAL'},
}

# Gateway links (dual-homed connections)
GATEWAY_LINKS = [
    {'id': 'gl1', 'source': 'gw_a', 'target': 's4', 'status': 'active', 'type': 'primary'},
    {'id': 'gl2', 'source': 'gw_a', 'target': 's5', 'status': 'active', 'type': 'backup'},
    {'id': 'gl3', 'source': 'gw_b', 'target': 's5', 'status': 'active', 'type': 'primary'},
    {'id': 'gl4', 'source': 'gw_b', 'target': 's6', 'status': 'active', 'type': 'backup'},
    {'id': 'gl5', 'source': 'gw_c', 'target': 's6', 'status': 'active', 'type': 'primary'},
    {'id': 'gl6', 'source': 'gw_c', 'target': 's4', 'status': 'active', 'type': 'backup'},
]

# Sensors matching topology.py
SENSORS = {
    'water_a1': {'id': 'water_a1', 'name': 'Water Level', 'type': 'flood', 'subtype': 'water_level',
                 'gateway': 'gw_a', 'switch': 's4', 'ip': '10.0.0.11',
                 'value': 20, 'threshold_warning': 50, 'threshold_emergency': 80, 'unit': 'cm',
                 'battery': 100, 'signal_strength': 95, 'status': 'NORMAL'},
    'rain_a2': {'id': 'rain_a2', 'name': 'Rainfall', 'type': 'flood', 'subtype': 'rainfall',
                'gateway': 'gw_a', 'switch': 's4', 'ip': '10.0.0.12',
                'value': 10, 'threshold_warning': 40, 'threshold_emergency': 70, 'unit': 'mm/hr',
                'battery': 100, 'signal_strength': 90, 'status': 'NORMAL'},
    'seismic_b1': {'id': 'seismic_b1', 'name': 'Seismic', 'type': 'earthquake', 'subtype': 'seismic',
                   'gateway': 'gw_b', 'switch': 's5', 'ip': '10.0.0.21',
                   'value': 5, 'threshold_warning': 30, 'threshold_emergency': 60, 'unit': 'Hz',
                   'battery': 100, 'signal_strength': 88, 'status': 'NORMAL'},
    'tilt_b2': {'id': 'tilt_b2', 'name': 'Tilt', 'type': 'earthquake', 'subtype': 'tilt',
                'gateway': 'gw_b', 'switch': 's5', 'ip': '10.0.0.22',
                'value': 2, 'threshold_warning': 15, 'threshold_emergency': 30, 'unit': 'deg',
                'battery': 100, 'signal_strength': 92, 'status': 'NORMAL'},
    'temp_c1': {'id': 'temp_c1', 'name': 'Temperature', 'type': 'fire', 'subtype': 'temperature',
                'gateway': 'gw_c', 'switch': 's6', 'ip': '10.0.0.31',
                'value': 25, 'threshold_warning': 45, 'threshold_emergency': 70, 'unit': '°C',
                'battery': 100, 'signal_strength': 85, 'status': 'NORMAL'},
    'smoke_c2': {'id': 'smoke_c2', 'name': 'Smoke', 'type': 'fire', 'subtype': 'smoke',
                 'gateway': 'gw_c', 'switch': 's6', 'ip': '10.0.0.32',
                 'value': 5, 'threshold_warning': 30, 'threshold_emergency': 60, 'unit': 'ppm',
                 'battery': 100, 'signal_strength': 87, 'status': 'NORMAL'},
}

# Display (Control Center) connects to all core switches
DISPLAY = {'id': 'display', 'name': 'Display/Control Center', 'ip': '10.0.0.100',
           'connected_switches': ['s1', 's2', 's3'], 'current_data': []}

# Packet statistics
PACKET_STATS = {'forwarded': 0, 'dropped': 0, 'total': 0}

def deepcopy_state():
    return {
        'switches': {k: dict(v) for k, v in SWITCHES.items()},
        'switch_links': [dict(l) for l in SWITCH_LINKS],
        'gateways': {k: dict(v) for k, v in GATEWAYS.items()},
        'gateway_links': [dict(l) for l in GATEWAY_LINKS],
        'sensors': {k: dict(v) for k, v in SENSORS.items()},
        'display': dict(DISPLAY),
        'current_intent': 'balanced',
        'event_logs': [],
        'routes': {},
        'auto_packets': True,
        'packet_stats': {'forwarded': 0, 'dropped': 0, 'total': 0}
    }

state = deepcopy_state()
packet_counter = 0

def get_timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def add_event_log(event_type, message, priority='INFO'):
    log = {'timestamp': get_timestamp(), 'type': event_type, 'message': message, 'priority': priority}
    state['event_logs'].insert(0, log)
    state['event_logs'] = state['event_logs'][:100]
    socketio.emit('event_log', log)
    return log

def classify_sensor_status(sensor):
    if sensor['value'] >= sensor['threshold_emergency']: return 'EMERGENCY'
    if sensor['value'] >= sensor['threshold_warning']: return 'WARNING'
    return 'NORMAL'

def classify_gateway_priority(gateway_id):
    gw = state['gateways'][gateway_id]
    max_p = 'NORMAL'
    for sid in gw['sensors']:
        s = state['sensors'][sid]
        if s['status'] == 'EMERGENCY': return 'EMERGENCY'
        if s['status'] == 'WARNING': max_p = 'WARNING'
    return max_p

def get_active_graph():
    """Build graph of active switches and links with dynamic costs"""
    graph = defaultdict(list)
    for link in state['switch_links']:
        if link['status'] == 'active':
            src_sw = state['switches'].get(link['source'])
            tgt_sw = state['switches'].get(link['target'])
            if src_sw and tgt_sw and src_sw['status'] == 'active' and tgt_sw['status'] == 'active':
                # Base weight from latency
                base_weight = link['latency']
                
                # Adjust weight based on intent
                if state['current_intent'] == 'low_latency':
                    w = base_weight * 0.5
                elif state['current_intent'] == 'low_power':
                    # Consider battery levels
                    src_battery = src_sw.get('battery', 100)
                    tgt_battery = tgt_sw.get('battery', 100)
                    battery_penalty = (200 - src_battery - tgt_battery) / 50
                    w = base_weight + battery_penalty + (1000 - link['bandwidth']) / 200
                elif state['current_intent'] == 'high_priority':
                    w = base_weight * 0.3  # Prefer faster routes
                else:  # balanced
                    w = base_weight + (1000 - link['bandwidth']) / 400
                
                # Add congestion factor based on active routes
                active_routes_on_link = sum(1 for r in state['routes'].values() 
                    if r and link['source'] in r.get('path', []) and link['target'] in r.get('path', []))
                w += active_routes_on_link * 0.5
                
                graph[link['source']].append((link['target'], w))
                graph[link['target']].append((link['source'], w))
    return graph

def dijkstra(graph, start, end_nodes):
    """Find shortest path from start to any of end_nodes"""
    all_nodes = set(state['switches'].keys())
    dists = {n: float('inf') for n in all_nodes}
    dists[start] = 0
    prev = {n: None for n in all_nodes}
    pq, visited = [(0, start)], set()
    
    while pq:
        d, cur = heapq.heappop(pq)
        if cur in visited: continue
        visited.add(cur)
        if cur in end_nodes: 
            path = []
            while cur: path.append(cur); cur = prev[cur]
            return path[::-1], d
        for nb, w in graph.get(cur, []):
            if nb not in visited and d + w < dists[nb]:
                dists[nb] = d + w
                prev[nb] = cur
                heapq.heappush(pq, (dists[nb], nb))
    return None, float('inf')

def compute_route(gateway_id, priority='NORMAL'):
    """Compute route from gateway to display through switches"""
    gw = state['gateways'][gateway_id]
    display_switches = state['display']['connected_switches']
    graph = get_active_graph()
    
    primary = gw['primary_switch']
    backup = gw['backup_switch']
    
    if state['switches'][primary]['status'] == 'active':
        start = primary
    elif state['switches'][backup]['status'] == 'active':
        start = backup
        add_event_log('FAILOVER', f'{gw["name"]} using backup {start}', 'WARNING')
    else:
        add_event_log('ERROR', f'{gw["name"]} has no available uplinks!', 'CRITICAL')
        return None, 'No uplinks'
    
    state['gateways'][gateway_id]['active_uplink'] = start
    
    path, cost = dijkstra(graph, start, set(display_switches))
    if not path:
        add_event_log('ERROR', f'No route from {gateway_id} to display', 'CRITICAL')
        return None, 'No route'
    
    # Add gateway-to-switch hop cost
    gw_to_sw_cost = 1.0
    if priority == 'EMERGENCY':
        gw_to_sw_cost = 0.5
    elif priority == 'WARNING':
        gw_to_sw_cost = 0.7
    
    total_cost = cost + gw_to_sw_cost
    
    reason = {
        'low_latency': 'Low latency path',
        'low_power': 'Energy efficient path',
        'high_priority': 'Priority routing'
    }.get(state['current_intent'], 'Balanced path')
    
    if priority == 'EMERGENCY': reason = 'Emergency priority routing'
    elif priority == 'WARNING': reason = 'Alert priority routing'
    
    return {
        'gateway': gateway_id,
        'path': [gateway_id] + path + ['display'],
        'switches_path': path,
        'cost': round(total_cost, 2),
        'reason': reason,
        'priority': priority,
        'intent': state['current_intent']
    }, None

@app.route('/api/topology', methods=['GET'])
def get_topology():
    return jsonify({
        'switches': state['switches'],
        'switch_links': state['switch_links'],
        'gateways': state['gateways'],
        'gateway_links': state['gateway_links'],
        'sensors': state['sensors'],
        'display': state['display'],
        'packet_stats': state['packet_stats']
    })

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    return jsonify(state['sensors'])

@app.route('/api/sensors/<sensor_id>', methods=['PUT'])
def update_sensor(sensor_id):
    if sensor_id not in state['sensors']: 
        return jsonify({'error': 'Not found'}), 404
    data = request.json
    sensor = state['sensors'][sensor_id]
    old_status = sensor['status']
    
    if 'value' in data: 
        sensor['value'] = max(0, min(100, int(data['value'])))
    
    sensor['status'] = classify_sensor_status(sensor)
    
    gw_id = sensor['gateway']
    old_gw_priority = state['gateways'][gw_id]['priority']
    state['gateways'][gw_id]['priority'] = classify_gateway_priority(gw_id)
    
    if sensor['status'] != old_status:
        prio_map = {'NORMAL': 'INFO', 'WARNING': 'WARNING', 'EMERGENCY': 'CRITICAL'}
        add_event_log('SENSOR', f'{sensor["name"]}: {old_status} -> {sensor["status"]} ({sensor["value"]}{sensor["unit"]})', prio_map[sensor['status']])
    
    if state['gateways'][gw_id]['priority'] != old_gw_priority:
        route, _ = compute_route(gw_id, state['gateways'][gw_id]['priority'])
        if route: state['routes'][gw_id] = route
    
    socketio.emit('sensor_update', {
        'sensor': sensor,
        'gateway': state['gateways'][gw_id],
        'routes': state['routes']
    })
    
    return jsonify(sensor)

@app.route('/api/gateways', methods=['GET'])
def get_gateways(): 
    return jsonify(state['gateways'])

@app.route('/api/switches', methods=['GET'])
def get_switches(): 
    return jsonify(state['switches'])

@app.route('/api/switches/<switch_id>/fail', methods=['POST'])
def fail_switch(switch_id):
    if switch_id not in state['switches']: 
        return jsonify({'error': 'Not found'}), 404
    state['switches'][switch_id]['status'] = 'failed'
    add_event_log('FAILURE', f'{switch_id.upper()} failed!', 'CRITICAL')
    
    for gw_id in state['gateways']:
        route, err = compute_route(gw_id, state['gateways'][gw_id]['priority'])
        if route: 
            state['routes'][gw_id] = route
            add_event_log('REROUTE', f'{gw_id}: {" -> ".join(route["path"])}', 'WARNING')
        elif err:
            # Packet would be dropped
            state['packet_stats']['dropped'] += 1
            state['packet_stats']['total'] += 1
    
    socketio.emit('topology_update', {
        'switches': state['switches'],
        'routes': state['routes'],
        'gateways': state['gateways'],
        'packet_stats': state['packet_stats']
    })
    return jsonify(state['switches'][switch_id])

@app.route('/api/switches/<switch_id>/restore', methods=['POST'])
def restore_switch(switch_id):
    if switch_id not in state['switches']: 
        return jsonify({'error': 'Not found'}), 404
    state['switches'][switch_id]['status'] = 'active'
    add_event_log('RESTORE', f'{switch_id.upper()} restored', 'INFO')
    
    for gw_id in state['gateways']:
        route, _ = compute_route(gw_id, state['gateways'][gw_id]['priority'])
        if route: state['routes'][gw_id] = route
    
    socketio.emit('topology_update', {
        'switches': state['switches'],
        'routes': state['routes'],
        'gateways': state['gateways']
    })
    return jsonify(state['switches'][switch_id])

@app.route('/api/links/<link_id>/fail', methods=['POST'])
def fail_link(link_id):
    for link in state['switch_links']:
        if link['id'] == link_id:
            link['status'] = 'failed'
            add_event_log('FAILURE', f'Link {link["source"].upper()}-{link["target"].upper()} failed!', 'CRITICAL')
            for gw_id in state['gateways']:
                route, err = compute_route(gw_id, state['gateways'][gw_id]['priority'])
                if route: 
                    state['routes'][gw_id] = route
                    add_event_log('REROUTE', f'{gw_id}: {" -> ".join(route["path"])}', 'WARNING')
                elif err:
                    state['packet_stats']['dropped'] += 1
                    state['packet_stats']['total'] += 1
            socketio.emit('topology_update', {
                'switch_links': state['switch_links'],
                'routes': state['routes'],
                'packet_stats': state['packet_stats']
            })
            return jsonify(link)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/links/<link_id>/restore', methods=['POST'])
def restore_link(link_id):
    for link in state['switch_links']:
        if link['id'] == link_id:
            link['status'] = 'active'
            add_event_log('RESTORE', f'Link {link["source"].upper()}-{link["target"].upper()} restored', 'INFO')
            for gw_id in state['gateways']:
                route, _ = compute_route(gw_id, state['gateways'][gw_id]['priority'])
                if route: state['routes'][gw_id] = route
            socketio.emit('topology_update', {
                'switch_links': state['switch_links'],
                'routes': state['routes']
            })
            return jsonify(link)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/intent', methods=['GET'])
def get_intent(): 
    return jsonify({'intent': state['current_intent']})

@app.route('/api/intent', methods=['PUT'])
def set_intent():
    data = request.json
    new_intent = data.get('intent', 'balanced')
    if new_intent not in ['balanced', 'low_latency', 'low_power', 'high_priority']: 
        return jsonify({'error': 'Invalid intent'}), 400
    
    old = state['current_intent']
    state['current_intent'] = new_intent
    add_event_log('INTENT', f'Changed: {old} -> {new_intent}', 'INFO')
    
    for gw_id in state['gateways']:
        route, _ = compute_route(gw_id, state['gateways'][gw_id]['priority'])
        if route: state['routes'][gw_id] = route
    
    socketio.emit('intent_update', {
        'intent': new_intent,
        'routes': state['routes']
    })
    return jsonify({'intent': new_intent, 'routes': state['routes']})

@app.route('/api/routes', methods=['GET'])
def get_routes(): 
    return jsonify(state['routes'])

@app.route('/api/events', methods=['GET'])
def get_events(): 
    return jsonify(state['event_logs'])

@app.route('/api/packet_stats', methods=['GET'])
def get_packet_stats():
    return jsonify(state['packet_stats'])

@app.route('/api/packets/generate', methods=['POST'])
def generate_packet():
    global packet_counter
    data = request.json
    gw_id = data.get('gateway_id')
    sensor_id = data.get('sensor_id')
    
    if not gw_id or gw_id not in state['gateways']: 
        return jsonify({'error': 'Invalid gateway'}), 400
    if not sensor_id or sensor_id not in state['sensors']: 
        return jsonify({'error': 'Invalid sensor'}), 400
    
    sensor = state['sensors'][sensor_id]
    route, err = compute_route(gw_id, sensor['status'])
    
    state['packet_stats']['total'] += 1
    
    if err: 
        state['packet_stats']['dropped'] += 1
        socketio.emit('packet_stats', state['packet_stats'])
        return jsonify({'error': err, 'dropped': True}), 500
    
    state['packet_stats']['forwarded'] += 1
    state['routes'][gw_id] = route
    packet_counter += 1
    
    # Update display with received data
    display_data = {
        'sensor_name': sensor['name'],
        'value': sensor['value'],
        'unit': sensor['unit'],
        'priority': sensor['status'],
        'timestamp': get_timestamp()
    }
    state['display']['current_data'].insert(0, display_data)
    state['display']['current_data'] = state['display']['current_data'][:6]
    
    packet = {
        'id': f'pkt_{packet_counter}',
        'sensor_id': sensor_id,
        'gateway_id': gw_id,
        'priority': sensor['status'],
        'path': route['path'],
        'data': {
            'type': sensor['type'],
            'value': sensor['value'],
            'unit': sensor['unit'],
            'sensor_name': sensor['name']
        },
        'route_reason': route['reason'],
        'cost': route['cost'],
        'timestamp': get_timestamp()
    }
    
    socketio.emit('new_packet', packet)
    socketio.emit('packet_stats', state['packet_stats'])
    socketio.emit('display_update', state['display'])
    return jsonify(packet)

@app.route('/api/auto_packets', methods=['POST'])
def toggle_auto_packets():
    state['auto_packets'] = not state['auto_packets']
    status = 'enabled' if state['auto_packets'] else 'disabled'
    add_event_log('SYSTEM', f'Auto packets {status}', 'INFO')
    socketio.emit('auto_packets_update', {'enabled': state['auto_packets']})
    return jsonify({'auto_packets': state['auto_packets']})

@app.route('/api/reset', methods=['POST'])
def reset_simulation():
    global state, packet_counter
    state = deepcopy_state()
    packet_counter = 0
    for gw_id in state['gateways']:
        route, _ = compute_route(gw_id, 'NORMAL')
        if route: state['routes'][gw_id] = route
    add_event_log('SYSTEM', 'Simulation reset', 'INFO')
    socketio.emit('simulation_reset', {**state, 'intent': state['current_intent']})
    return jsonify({'message': 'Reset successful'})

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to SADRN'})
    emit('topology_data', {
        'switches': state['switches'],
        'switch_links': state['switch_links'],
        'gateways': state['gateways'],
        'gateway_links': state['gateway_links'],
        'sensors': state['sensors'],
        'display': state['display'],
        'routes': state['routes'],
        'intent': state['current_intent'],
        'auto_packets': state['auto_packets'],
        'packet_stats': state['packet_stats']
    })

@socketio.on('request_topology')
def handle_topology_request():
    emit('topology_data', {
        'switches': state['switches'],
        'switch_links': state['switch_links'],
        'gateways': state['gateways'],
        'gateway_links': state['gateway_links'],
        'sensors': state['sensors'],
        'display': state['display'],
        'routes': state['routes'],
        'intent': state['current_intent'],
        'auto_packets': state['auto_packets'],
        'packet_stats': state['packet_stats']
    })

def auto_packet_sender():
    """Send packets automatically from all sensors"""
    global packet_counter
    while True:
        time.sleep(2)
        if not state['auto_packets']:
            continue
        
        sensor_id = random.choice(list(state['sensors'].keys()))
        sensor = state['sensors'][sensor_id]
        gw_id = sensor['gateway']
        
        route, err = compute_route(gw_id, sensor['status'])
        
        state['packet_stats']['total'] += 1
        
        if err:
            state['packet_stats']['dropped'] += 1
            socketio.emit('packet_stats', state['packet_stats'])
            continue
        
        state['packet_stats']['forwarded'] += 1
        state['routes'][gw_id] = route
        packet_counter += 1
        
        display_data = {
            'sensor_name': sensor['name'],
            'value': sensor['value'],
            'unit': sensor['unit'],
            'priority': sensor['status'],
            'timestamp': get_timestamp()
        }
        state['display']['current_data'].insert(0, display_data)
        state['display']['current_data'] = state['display']['current_data'][:6]
        
        packet = {
            'id': f'pkt_{packet_counter}',
            'sensor_id': sensor_id,
            'gateway_id': gw_id,
            'priority': sensor['status'],
            'path': route['path'],
            'data': {
                'type': sensor['type'],
                'value': sensor['value'],
                'unit': sensor['unit'],
                'sensor_name': sensor['name']
            },
            'route_reason': route['reason'],
            'cost': route['cost'],
            'timestamp': get_timestamp()
        }
        
        socketio.emit('new_packet', packet)
        socketio.emit('packet_stats', state['packet_stats'])
        socketio.emit('display_update', state['display'])

if __name__ == '__main__':
    print("="*60)
    print("SADRN Backend Starting")
    print("  API: http://0.0.0.0:5000")
    print("  WebSocket enabled")
    print("="*60)
    
    for gw_id in state['gateways']:
        route, _ = compute_route(gw_id, 'NORMAL')
        if route: state['routes'][gw_id] = route
    
    threading.Thread(target=auto_packet_sender, daemon=True).start()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
