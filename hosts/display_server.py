#!/usr/bin/env python3
"""
SADRN Display Server - Central Monitoring
Receives data from all gateways, processes with priority ordering,
and reports to dashboard backend for visualization
"""

import socket
import json
import time
import threading
import argparse
import signal
import sys
import requests
from collections import deque, OrderedDict
from datetime import datetime

class DisplayServer:
    def __init__(self, listen_port=9001, dashboard_url='http://localhost:5000'):
        self.listen_port = listen_port
        self.dashboard_url = dashboard_url
        self.running = True
        
        # UDP socket for receiving from gateways
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_sock.bind(('0.0.0.0', listen_port))
        self.recv_sock.settimeout(1.0)
        
        # Message storage with priority
        self.messages = OrderedDict()
        self.message_history = deque(maxlen=100)
        self.alerts = deque(maxlen=50)
        self.lock = threading.Lock()
        
        # Statistics
        self.total_received = 0
        self.emergency_count = 0
        self.normal_count = 0
        
        # Flow tracking
        self.flows = deque(maxlen=100)
        
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
    
    def stop(self, *args):
        self.running = False
        print("\n[DISPLAY] Shutting down...")
        self.print_stats()
        sys.exit(0)
    
    def print_stats(self):
        print("[DISPLAY] Final Statistics:")
        print(f"  Total Received: {self.total_received}")
        print(f"  Emergency: {self.emergency_count}")
        print(f"  Normal: {self.normal_count}")
    
    def process_packet(self, data, addr):
        """Process incoming packet from gateway"""
        try:
            packet = json.loads(data.decode('utf-8'))
            self.total_received += 1
            
            sensor_id = packet.get('sensor_id', 'unknown')
            value = packet.get('value', 0)
            unit = packet.get('unit', '')
            priority = packet.get('priority', 'normal')
            gateway_id = packet.get('gateway_id', 'unknown')
            is_alert = packet.get('is_alert', False)
            source_ip = packet.get('source_ip', addr[0])
            
            # Determine priority
            actual_priority = 'emergency' if is_alert else priority
            
            # Track as flow
            flow = {
                'source': source_ip,
                'destination': self.get_own_ip(),
                'gateway': gateway_id,
                'sensor_type': sensor_id,
                'value': value,
                'unit': unit,
                'priority': actual_priority,
                'is_alert': is_alert
            }
            
            with self.lock:
                self.flows.append(flow)
                
                # Update latest sensor reading
                self.messages[sensor_id] = {
                    'sensor_id': sensor_id,
                    'value': value,
                    'unit': unit,
                    'priority': actual_priority,
                    'gateway': gateway_id,
                    'is_alert': is_alert,
                    'timestamp': datetime.now().isoformat()
                }
                
                if is_alert:
                    self.emergency_count += 1
                else:
                    self.normal_count += 1
            
            # Print with priority formatting
            if is_alert:
                print(f"\033[91m[EMERGENCY] {sensor_id} via {gateway_id}: {value:.2f} {unit}\033[0m")
            else:
                print(f"\033[92m[NORMAL] {sensor_id} via {gateway_id}: {value:.2f} {unit}\033[0m")
            
            # Send to dashboard backend
            self.send_to_dashboard(flow)
            
        except Exception as e:
            print(f"[DISPLAY] Error processing packet: {e}")
    
    def get_own_ip(self):
        """Get own IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.0.0.1', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "10.0.0.100"
    
    def send_to_dashboard(self, packet_data):
        """Send data to dashboard backend via HTTP"""
        try:
            requests.post(f"{self.dashboard_url}/api/packet", json=packet_data, timeout=1)
        except Exception as e:
            pass  # Dashboard might not be running
    
    def get_priority_ordered_display(self):
        """Get all messages ordered by priority (emergency first)"""
        with self.lock:
            priority_order = {'emergency': 0, 'high': 1, 'normal': 2, 'low': 3}
            sorted_messages = sorted(
                self.messages.values(),
                key=lambda m: (priority_order.get(m.get('priority', 'normal'), 2))
            )
            return sorted_messages
    
    def display_status(self):
        """Periodic status display"""
        while self.running:
            time.sleep(10)
            print("\n" + "="*60)
            print("[DISPLAY] Current Sensor Status (Priority Ordered):")
            print("="*60)
            for msg in self.get_priority_ordered_display():
                status = "🚨 ALERT" if msg.get('is_alert') else "✓ Normal"
                print(f"  {msg['sensor_id']:15} | {msg['value']:8.2f} {msg['unit']:6} | {status}")
            print("="*60 + "\n")
    
    def run(self):
        """Main display server loop"""
        print("[DISPLAY] Starting Display Server")
        print(f"[DISPLAY] Listening on port {self.listen_port}")
        print(f"[DISPLAY] Dashboard API: {self.dashboard_url}")
        print("[DISPLAY] Waiting for sensor data...\n")
        
        # Start status display thread
        status_thread = threading.Thread(target=self.display_status, daemon=True)
        status_thread.start()
        
        while self.running:
            try:
                data, addr = self.recv_sock.recvfrom(4096)
                self.process_packet(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[DISPLAY] Receive error: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SADRN Display Server')
    parser.add_argument('--port', type=int, default=9001, help='Listen port')
    parser.add_argument('--dashboard', default='http://localhost:5000', 
                       help='Dashboard backend URL')
    
    args = parser.parse_args()
    
    server = DisplayServer(
        listen_port=args.port,
        dashboard_url=args.dashboard
    )
    
    server.run()
