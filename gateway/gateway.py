#!/usr/bin/env python3
"""
SADRN Gateway - Simplified version

Usage: python3 gateway.py <ID>
  ID: A=Flood(5001), B=Earthquake(5002), C=Fire(5003)
"""

import sys, json, threading, time
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify
import requests

# Gateway configuration
GATEWAY_CONFIG = {
    'A': {'type': 'flood', 'port': 5001, 'priority': 1},
    'B': {'type': 'earthquake', 'port': 5002, 'priority': 3},
    'C': {'type': 'fire', 'port': 5003, 'priority': 2}
}

DISPLAY_URL = "http://10.0.0.100:8080/data"

app = Flask(__name__)

state = {
    'id': None, 'type': None, 'port': None,
    'readings': 0, 'emergencies': 0, 'data': deque(maxlen=50)
}


def forward_to_display(data):
    try:
        requests.post(DISPLAY_URL, json=data, timeout=2)
    except:
        pass


@app.route('/sensor_data', methods=['POST'])
def receive_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'no data'}), 400
    
    state['readings'] += 1
    if data.get('is_emergency'):
        state['emergencies'] += 1
    
    # Add gateway info
    data['gateway_id'] = state['id']
    data['gateway_type'] = state['type']
    data['gateway_timestamp'] = datetime.now().isoformat()
    
    state['data'].append(data)
    
    status = "ALERT" if data.get('is_emergency') else "OK"
    print(f"[GW-{state['id']}] {status}: {data.get('sensor_type')} = {data.get('value')} {data.get('unit')}")
    
    # Forward to display
    threading.Thread(target=forward_to_display, args=(data,), daemon=True).start()
    
    return jsonify({'status': 'ok'}), 200


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'id': state['id'], 'type': state['type'],
        'readings': state['readings'], 'emergencies': state['emergencies']
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    gw_id = sys.argv[1].upper() if len(sys.argv) > 1 else 'A'
    
    if gw_id not in GATEWAY_CONFIG:
        print(f"Unknown gateway ID: {gw_id}. Use A, B, or C.")
        sys.exit(1)
    
    config = GATEWAY_CONFIG[gw_id]
    state['id'] = gw_id
    state['type'] = config['type']
    state['port'] = config['port']
    
    print("=" * 50)
    print(f"SADRN GATEWAY {gw_id} - {config['type'].upper()}")
    print(f"Listening on port {config['port']}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=config['port'], debug=False, threaded=True)
