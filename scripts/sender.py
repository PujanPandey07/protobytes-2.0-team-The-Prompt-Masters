#!/usr/bin/env python3
"""
SADRN - Sender Script for sensor hosts (h1, h2, h3)
Generates UDP traffic to the Display Node
"""

import socket
import json
import time
import sys
import threading
import signal
from datetime import datetime

DISPLAY_NODE_IP = '10.0.0.100'
NORMAL_PORT = 5000
EMERGENCY_PORT = 5001
DSCP_EMERGENCY = 46
NORMAL_RATE = 1
EMERGENCY_RATE = 5
CONTROL_PORT = 6000


class SensorSender:
    def __init__(self, host_id):
        self.host_id = host_id
        self.running = True
        self.emergency_mode = False
        self.disaster_type = None
        self.packets_sent = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        signal.signal(signal.SIGINT, lambda s, f: setattr(self, 'running', False))
        signal.signal(signal.SIGTERM, lambda s, f: setattr(self, 'running', False))
        print(f"[{self.host_id}] Sender initialized")
    
    def send_packet(self, seq):
        port = EMERGENCY_PORT if self.emergency_mode else NORMAL_PORT
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, (DSCP_EMERGENCY if self.emergency_mode else 0) << 2)
        
        packet = json.dumps({
            'type': 'sensor_data', 'host_id': self.host_id, 'sequence': seq,
            'timestamp': datetime.now().isoformat(),
            'priority': 'CRITICAL' if self.emergency_mode else 'NORMAL',
            'emergency': self.emergency_mode, 'disaster_type': self.disaster_type,
            'data': {'temperature': 25 + (seq % 10), 'humidity': 60 + (seq % 20),
                     'smoke_level': 100 if self.emergency_mode and self.disaster_type == 'fire' else 0,
                     'water_level': 100 if self.emergency_mode and self.disaster_type == 'flood' else 0,
                     'vibration': 100 if self.emergency_mode and self.disaster_type == 'earthquake' else 0}
        }).encode('utf-8')
        
        try:
            self.sock.sendto(packet, (DISPLAY_NODE_IP, port))
            self.packets_sent += 1
            priority = "CRITICAL" if self.emergency_mode else "NORMAL"
            print(f"[{self.host_id}] [{priority}] Sent #{seq} -> {DISPLAY_NODE_IP}:{port}")
        except Exception as e:
            print(f"[{self.host_id}] ERROR: {e}")
    
    def run_sender(self):
        print(f"[{self.host_id}] Starting sender to {DISPLAY_NODE_IP}")
        seq = 0
        while self.running:
            self.send_packet(seq)
            seq += 1
            time.sleep(1.0 / (EMERGENCY_RATE if self.emergency_mode else NORMAL_RATE))
        print(f"[{self.host_id}] Stopped. Packets sent: {self.packets_sent}")
    
    def run_control_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        port = CONTROL_PORT + int(self.host_id[1])
        try:
            sock.bind(('', port))
            print(f"[{self.host_id}] Control on port {port}")
        except:
            return
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                cmd = json.loads(data.decode('utf-8'))
                if cmd.get('action') == 'set_emergency':
                    self.emergency_mode = cmd.get('enabled', False)
                    self.disaster_type = cmd.get('disaster_type') if self.emergency_mode else None
                    print(f"[{self.host_id}] Emergency: {self.emergency_mode}")
                    sock.sendto(json.dumps({'status': 'ok'}).encode(), addr)
                elif cmd.get('action') == 'stop':
                    self.running = False
            except socket.timeout:
                pass
        sock.close()
    
    def run(self):
        threading.Thread(target=self.run_control_server, daemon=True).start()
        self.run_sender()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python sender.py <host_id>")
        sys.exit(1)
    SensorSender(sys.argv[1]).run()
