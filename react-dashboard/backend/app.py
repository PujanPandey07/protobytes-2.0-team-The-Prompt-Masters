"""
SADRN Flask Backend - Optimized Controller
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading, time, heapq, random
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Topology Configuration
SWITCHES = {
    's1': {'id': 's1', 'name': 'Core Switch 1', 'type': 'core', 'status': 'active', 'battery': 100},
    's2': {'id': 's2', 'name': 'Core Switch 2', 'type': 'core', 'status': 'active', 'battery': 100},
    's3': {'id': 's3', 'name': 'Core Switch 3', 'type': 'core', 'status': 'active', 'battery': 100},
    's4': {'id': 's4', 'name': 'Zone A Switch', 'type': 'zone', 'status': 'active', 'battery': 100},
    's5': {'id': 's5', 'name': 'Zone B Switch', 'type': 'zone', 'status': 'active', 'battery': 100},
    's6': {'id': 's6', 'name': 'Zone C Switch', 'type': 'zone', 'status': 'active', 'battery': 100},
}

SWITCH_LINKS = [
    {'id': 'l1', 'source': 's1', 'target': 's2', 'status': 'active', 'latency': 2, 'type': 'core', 'bandwidth': 1000},
    {'id': 'l2', 'source': 's2', 'target': 's3', 'status': 'active', 'latency': 2, 'type': 'core', 'bandwidth': 1000},
    {'id': 'l3', 'source': 's3', 'target': 's1', 'status': 'active', 'latency': 2, 'type': 'core', 'bandwidth': 1000},
    {'id': 'l4', 'source': 's4', 'target': 's1', 'status': 'active', 'latency': 3, 'type': 'zone', 'bandwidth': 100},
    {'id': 'l5', 'source': 's5', 'target': 's2', 'status': 'active', 'latency': 3, 'type': 'zone', 'bandwidth': 100},
    {'id': 'l6', 'source': 's6', 'target': 's3', 'status': 'active', 'latency': 3, 'type': 'zone', 'bandwidth': 100},
]

GATEWAYS = {
    'gw_a': {'id': 'gw_a', 'name': 'Gateway A', 'ip': '10.0.0.1', 'status': 'active',
             'primary_switch': 's4', 'backup_switch': 's5', 'active_uplink': 's4',
             'sensors': ['water_a1', 'rain_a2'], 'priority': 'NORMAL'},
    'gw_b': {'id': 'gw_b', 'name': 'Gateway B', 'ip': '10.0.0.2', 'status': 'active',
             'primary_switch': 's5', 'backup_switch': 's6', 'active_uplink': 's5',
             'sensors': ['seismic_b1', 'tilt_b2'], 'priority': 'NORMAL'},
    'gw_c': {'id': 'gw_c', 'name': 'Gateway C', 'ip': '10.0.0.3', 'status': 'active',
             'primary_switch': 's6', 'backup_switch': 's4', 'active_uplink': 's6',
             'sensors': ['temp_c1', 'smoke_c2'], 'priority': 'NORMAL'},
}

GATEWAY_LINKS = [
    {'id': 'gl1', 'source': 'gw_a', 'target': 's4', 'status': 'active', 'type': 'primary'},
    {'id': 'gl2', 'source': 'gw_a', 'target': 's5', 'status': 'active', 'type': 'backup'},
    {'id': 'gl3', 'source': 'gw_b', 'target': 's5', 'status': 'active', 'type': 'primary'},
    {'id': 'gl4', 'source': 'gw_b', 'target': 's6', 'status': 'active', 'type': 'backup'},
    {'id': 'gl5', 'source': 'gw_c', 'target': 's6', 'status': 'active', 'type': 'primary'},
    {'id': 'gl6', 'source': 'gw_c', 'target': 's4', 'status': 'active', 'type': 'backup'},
]

SENSORS = {
    'water_a1': {'id': 'water_a1', 'name': 'Water Level', 'type': 'flood', 'gateway': 'gw_a',
                 'value': 25, 'threshold_warning': 50, 'threshold_emergency': 80, 'unit': 'cm', 'status': 'NORMAL'},
    'rain_a2': {'id': 'rain_a2', 'name': 'Rainfall', 'type': 'flood', 'gateway': 'gw_a',
                'value': 15, 'threshold_warning': 40, 'threshold_emergency': 70, 'unit': 'mm/hr', 'status': 'NORMAL'},
    'seismic_b1': {'id': 'seismic_b1', 'name': 'Seismic', 'type': 'earthquake', 'gateway': 'gw_b',
                   'value': 8, 'threshold_warning': 30, 'threshold_emergency': 60, 'unit': 'Hz', 'status': 'NORMAL'},
    'tilt_b2': {'id': 'tilt_b2', 'name': 'Tilt', 'type': 'earthquake', 'gateway': 'gw_b',
                'value': 3, 'threshold_warning': 15, 'threshold_emergency': 30, 'unit': '°', 'status': 'NORMAL'},
    'temp_c1': {'id': 'temp_c1', 'name': 'Temperature', 'type': 'fire', 'gateway': 'gw_c',
                'value': 28, 'threshold_warning': 45, 'threshold_emergency': 70, 'unit': '°C', 'status': 'NORMAL'},
    'smoke_c2': {'id': 'smoke_c2', 'name': 'Smoke', 'type': 'fire', 'gateway': 'gw_c',
                 'value': 8, 'threshold_warning': 30, 'threshold_emergency': 60, 'unit': 'ppm', 'status': 'NORMAL'},
}

DISPLAY = {'id': 'display', 'name': 'Control Center', 'ip': '10.0.0.100',
           'connected_switches': ['s1', 's2', 's3'], 'current_data': []}

# State
def deepcopy_state():
    return {
        'switches': {k: dict(v) for k, v in SWITCHES.items()},
        'switch_links': [dict(l) for l in SWITCH_LINKS],
        'gateways': {k: dict(v) for k, v in GATEWAYS.items()},
        'gateway_links': [dict(l) for l in GATEWAY_LINKS],
        'sensors': {k: dict(v) for k, v in SENSORS.items()},
        'display': {**DISPLAY, 'current_data': []},
        'current_intent': 'balanced',
        'event_logs': [],
        'routes': {},
        'auto_packets': True,
        'auto_intent': True,
        'packet_stats': {'forwarded': 0, 'dropped': 0, 'total': 0}
    }

state = deepcopy_state()
packet_counter = 0

# Helpers
def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")

def add_event_log(event_type, message, priority='INFO'):
    log = {'timestamp': get_timestamp(), 'type': event_type, 'message': message, 'priority': priority}
    state['event_logs'].insert(0, log)
    state['event_logs'] = state['event_logs'][:50]
    socketio.emit('event_log', log)
    return log

def classify_sensor_status(sensor):
    if sensor['value'] >= sensor['threshold_emergency']: return 'EMERGENCY'
    if sensor['value'] >= sensor['threshold_warning']: return 'WARNING'
    return 'NORMAL'

def classify_gateway_priority(gateway_id):
    gw = state['gateways'][gateway_id]
    for sid in gw['sensors']:
        s = state['sensors'][sid]
        if s['status'] == 'EMERGENCY': return 'EMERGENCY'
    for sid in gw['sensors']:
        s = state['sensors'][sid]
        if s['status'] == 'WARNING': return 'WARNING'
    return 'NORMAL'

def determine_auto_intent():
    has_emergency = any(s['status'] == 'EMERGENCY' for s in state['sensors'].values())
    has_warning = any(s['status'] == 'WARNING' for s in state['sensors'].values())
    if has_emergency: return 'high_priority'
    if has_warning: return 'low_latency'
    return 'balanced'

# Routing - Unified Cost Function
def get_battery_penalty(switch_id):
    battery = state['switches'][switch_id].get('battery', 100)
    if battery < 20: return 30
    if battery < 40: return 15
    return 0

def get_active_graph():
    """Build weighted graph with unified cost function"""
    graph = defaultdict(list)
    intent = state['current_intent']
    
    # Intent weights: (latency_w, battery_w)
    weights = {'high_priority': (0.95, 0.05), 'low_latency': (0.7, 0.3), 'balanced': (0.25, 0.75)}
    lat_w, bat_w = weights.get(intent, (0.5, 0.5))
    
    for link in state['switch_links']:
        if link['status'] != 'active':
            continue
        src_sw = state['switches'].get(link['source'])
        tgt_sw = state['switches'].get(link['target'])
        if not (src_sw and tgt_sw and src_sw['status'] == 'active' and tgt_sw['status'] == 'active'):
            continue
        
        # Unified cost = latency_weight * latency + battery_weight * battery_penalty
        latency = link['latency']
        battery_penalty = (get_battery_penalty(link['source']) + get_battery_penalty(link['target'])) / 2
        cost = lat_w * latency + bat_w * battery_penalty
        
        graph[link['source']].append((link['target'], max(cost, 0.1)))
        graph[link['target']].append((link['source'], max(cost, 0.1)))
    
    return graph

def dijkstra(graph, start, end_nodes):
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
    gw = state['gateways'][gateway_id]
    display_switches = set(state['display']['connected_switches'])
    graph = get_active_graph()
    
    # Determine start switch
    primary = gw['primary_switch']
    backup = gw['backup_switch']
    primary_ok = state['switches'][primary]['status'] == 'active'
    backup_ok = state['switches'][backup]['status'] == 'active'
    
    if primary_ok and state['switches'][primary].get('battery', 100) >= 15:
        start = primary
    elif backup_ok:
        start = backup
    elif primary_ok:
        start = primary
    else:
        return None, 'No uplinks'
    
    state['gateways'][gateway_id]['active_uplink'] = start
    
    path, cost = dijkstra(graph, start, display_switches)
    if not path:
        return None, 'No route'
    
    return {
        'gateway': gateway_id,
        'path': [gateway_id] + path + ['display'],
        'switches_path': path,
        'cost': round(cost, 2),
        'priority': priority,
        'intent': state['current_intent'],
        'reason': f'{state["current_intent"]} routing'
    }, None

def recompute_all_routes():
    for gw_id in state['gateways']:
        route, _ = compute_route(gw_id, state['gateways'][gw_id]['priority'])
        if route:
            state['routes'][gw_id] = route

# API Routes
@app.route('/api/topology', methods=['GET'])
def get_topology():
    return jsonify({
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
    state['gateways'][gw_id]['priority'] = classify_gateway_priority(gw_id)
    
    if sensor['status'] != old_status:
        add_event_log('SENSOR', f'{sensor["name"]}: {old_status} → {sensor["status"]}', 
                      'CRITICAL' if sensor['status'] == 'EMERGENCY' else 'WARNING' if sensor['status'] == 'WARNING' else 'INFO')
    
    # Update intent (auto mode only)
    old_intent = state['current_intent']
    if state.get('auto_intent', True):
        state['current_intent'] = determine_auto_intent()
    if old_intent != state['current_intent']:
        add_event_log('INTENT', f'Intent changed to {state["current_intent"]}', 'WARNING')
        recompute_all_routes()
    
    socketio.emit('sensor_update', {'sensor': sensor, 'gateway': state['gateways'][gw_id], 'routes': state['routes'], 'intent': state['current_intent']})
    return jsonify(sensor)

@app.route('/api/switches/<switch_id>/battery', methods=['PUT'])
def update_switch_battery(switch_id):
    if switch_id not in state['switches']:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.json
    old_battery = state['switches'][switch_id]['battery']
    new_battery = max(0, min(100, int(data.get('battery', old_battery))))
    state['switches'][switch_id]['battery'] = new_battery
    
    if old_battery >= 20 > new_battery:
        add_event_log('BATTERY', f'{switch_id.upper()} CRITICAL ({new_battery}%)', 'CRITICAL')
    
    recompute_all_routes()
    socketio.emit('topology_update', {'switches': state['switches'], 'routes': state['routes']})
    return jsonify(state['switches'][switch_id])

@app.route('/api/switches/<switch_id>/fail', methods=['POST'])
def fail_switch(switch_id):
    if switch_id not in state['switches']:
        return jsonify({'error': 'Not found'}), 404
    state['switches'][switch_id]['status'] = 'failed'
    add_event_log('FAILURE', f'{switch_id.upper()} FAILED', 'CRITICAL')
    recompute_all_routes()
    socketio.emit('topology_update', {'switches': state['switches'], 'routes': state['routes'], 'gateways': state['gateways']})
    return jsonify(state['switches'][switch_id])

@app.route('/api/switches/<switch_id>/restore', methods=['POST'])
def restore_switch(switch_id):
    if switch_id not in state['switches']:
        return jsonify({'error': 'Not found'}), 404
    state['switches'][switch_id]['status'] = 'active'
    add_event_log('RESTORE', f'{switch_id.upper()} restored', 'INFO')
    recompute_all_routes()
    socketio.emit('topology_update', {'switches': state['switches'], 'routes': state['routes'], 'gateways': state['gateways']})
    return jsonify(state['switches'][switch_id])

@app.route('/api/links/<link_id>/fail', methods=['POST'])
def fail_link(link_id):
    for link in state['switch_links']:
        if link['id'] == link_id:
            link['status'] = 'failed'
            add_event_log('FAILURE', f'Link {link["source"]}-{link["target"]} FAILED', 'CRITICAL')
            recompute_all_routes()
            socketio.emit('topology_update', {'switch_links': state['switch_links'], 'routes': state['routes']})
            return jsonify(link)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/links/<link_id>/restore', methods=['POST'])
def restore_link(link_id):
    for link in state['switch_links']:
        if link['id'] == link_id:
            link['status'] = 'active'
            add_event_log('RESTORE', f'Link {link["source"]}-{link["target"]} restored', 'INFO')
            recompute_all_routes()
            socketio.emit('topology_update', {'switch_links': state['switch_links'], 'routes': state['routes']})
            return jsonify(link)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/intent', methods=['GET'])
def get_intent():
    return jsonify({"intent": state["current_intent"], "auto_intent": state.get("auto_intent", True)})

@app.route("/api/intent", methods=["PUT"])
def set_intent():
    data = request.json
    new_intent = data.get("intent")
    auto = data.get("auto", None)
    
    if auto is not None:
        state["auto_intent"] = auto
    
    if new_intent in ["high_priority", "low_latency", "balanced"]:
        old_intent = state["current_intent"]
        state["current_intent"] = new_intent
        if old_intent != new_intent:
            add_event_log("INTENT", f"Manual intent: {new_intent}", "WARNING")
            recompute_all_routes()
    
    socketio.emit("intent_update", {"intent": state["current_intent"], "auto_intent": state.get("auto_intent", True), "routes": state["routes"]})
    return jsonify({"intent": state["current_intent"], "auto_intent": state.get("auto_intent", True)})

@app.route('/api/routes', methods=['GET'])
def get_routes():
    return jsonify(state['routes'])

@app.route('/api/events', methods=['GET'])
def get_events():
    return jsonify(state['event_logs'])

@app.route('/api/packet_stats', methods=['GET'])
def get_packet_stats():
    return jsonify(state['packet_stats'])

@app.route('/api/auto_packets', methods=['POST'])
def toggle_auto_packets():
    state['auto_packets'] = not state['auto_packets']
    socketio.emit('auto_packets_update', {'enabled': state['auto_packets']})
    return jsonify({'auto_packets': state['auto_packets']})

@app.route('/api/reset', methods=['POST'])
def reset_simulation():
    global state, packet_counter
    state = deepcopy_state()
    packet_counter = 0
    recompute_all_routes()
    add_event_log('SYSTEM', 'Simulation reset', 'INFO')
    socketio.emit('simulation_reset', {**state, 'intent': state['current_intent']})
    return jsonify({'message': 'Reset'})

# WebSocket
@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected'})
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

# Background Threads
def auto_packet_sender():
    global packet_counter
    sensor_ids = list(SENSORS.keys())
    idx = 0
    
    while True:
        time.sleep(2.5)  # Slower rate
        if not state['auto_packets']:
            continue
        
        # Round-robin through sensors, prioritize emergencies
        emergency_sensors = [s for s in sensor_ids if state['sensors'][s]['status'] == 'EMERGENCY']
        warning_sensors = [s for s in sensor_ids if state['sensors'][s]['status'] == 'WARNING']
        
        if emergency_sensors:
            sensor_id = random.choice(emergency_sensors)
        elif warning_sensors and random.random() < 0.6:
            sensor_id = random.choice(warning_sensors)
        else:
            sensor_id = sensor_ids[idx % len(sensor_ids)]
            idx += 1
        
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
        
        # Update display
        display_data = {
            'sensor_id': sensor_id,
            'sensor_name': sensor['name'],
            'value': sensor['value'],
            'unit': sensor['unit'],
            'priority': sensor['status'],
            'timestamp': get_timestamp()
        }
        state['display']['current_data'].insert(0, display_data)
        state['display']['current_data'] = state['display']['current_data'][:4]
        
        packet = {
            'id': f'pkt_{packet_counter}',
            'sensor_id': sensor_id,
            'gateway_id': gw_id,
            'priority': sensor['status'],
            'path': route['path'],
            'data': {'type': sensor['type'], 'value': sensor['value'], 'unit': sensor['unit'], 'sensor_name': sensor['name']},
            'cost': route['cost'],
            'timestamp': get_timestamp()
        }
        
        socketio.emit('new_packet', packet)
        socketio.emit('packet_stats', state['packet_stats'])
        socketio.emit('display_update', state['display'])

def battery_drain():
    while True:
        time.sleep(30)
        for sw_id, sw in state['switches'].items():
            if sw['status'] == 'active' and sw['battery'] > 0:
                drain = 0.5
                for route in state['routes'].values():
                    if route and sw_id in route.get('switches_path', []):
                        drain += 0.3
                sw['battery'] = max(0, sw['battery'] - drain)
        socketio.emit('battery_update', {'switches': {k: {'battery': round(v['battery'], 1)} for k, v in state['switches'].items()}})

if __name__ == '__main__':
    print("="*50)
    print("SADRN Backend - Optimized")
    print("  API: http://0.0.0.0:5000")
    print("="*50)
    
    recompute_all_routes()
    
    threading.Thread(target=auto_packet_sender, daemon=True).start()
    threading.Thread(target=battery_drain, daemon=True).start()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
