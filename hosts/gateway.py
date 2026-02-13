#!/usr/bin/env python3
"""
SADRN Gateway Node - Local Aggregation Gateway
Receives data from sensors, aggregates, and forwards to Display Server
Demonstrates intermediate routing in SDN network
"""

import socket
import json
import time
import threading
import argparse
import signal
import sys
from collections import deque

class GatewayNode:
    def __init__(self, gateway_id, listen_port, display_ip, display_port=9001):
        self.gateway_id = gateway_id
        self.listen_port = listen_port
        self.display_ip = display_ip
        self.display_port = display_port
        self.running = True
        
        # UDP sockets
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_sock.bind(('0.0.0.0', listen_port))
        self.recv_sock.settimeout(1.0)
        
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Statistics
        self.packets_received = 0
        self.packets_forwarded = 0
        self.packets_dropped = 0
        
        # Aggregation buffer
        self.buffer = deque(maxlen=100)
        self.buffer_lock = threading.Lock()
        
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
    
    def stop(self, *args):
        self.running = False
        print(f"[{self.gateway_id}] Shutting down...")
        self.print_stats()
        sys.exit(0)
    
    def print_stats(self):
        print(f"[{self.gateway_id}] Statistics:")
        print(f"  Received: {self.packets_received}")
        print(f"  Forwarded: {self.packets_forwarded}")
        print(f"  Dropped: {self.packets_dropped}")
    
    def get_own_ip(self):
        """Get own IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.display_ip, 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"
    
    def process_sensor_data(self, data, addr):
        """Process incoming sensor data"""
        try:
            packet = json.loads(data.decode('utf-8'))
            self.packets_received += 1
            
            # Add gateway info
            packet['gateway_id'] = self.gateway_id
            packet['gateway_ip'] = self.get_own_ip()
            packet['gateway_timestamp'] = time.time()
            packet['hop_count'] = packet.get('hop_count', 0) + 1
            
            # Log
            sensor_id = packet.get('sensor_id', 'unknown')
            value = packet.get('value', 0)
            priority = packet.get('priority', 'normal')
            print(f"[{self.gateway_id}] Received from {sensor_id}: {value} ({priority})")
            
            # Forward to display server
            self.forward_to_display(packet)
            
        except Exception as e:
            print(f"[{self.gateway_id}] Error processing packet: {e}")
            self.packets_dropped += 1
    
    def forward_to_display(self, packet):
        """Forward packet to display server through SDN network"""
        try:
            data = json.dumps(packet).encode('utf-8')
            self.send_sock.sendto(data, (self.display_ip, self.display_port))
            self.packets_forwarded += 1
            
            sensor_id = packet.get('sensor_id', 'unknown')
            priority = packet.get('priority', 'normal')
            print(f"[{self.gateway_id}] Forwarded {sensor_id} to display ({priority})")
            
        except Exception as e:
            print(f"[{self.gateway_id}] Failed to forward: {e}")
            self.packets_dropped += 1
    
    def run(self):
        """Main gateway loop"""
        print(f"[{self.gateway_id}] Starting gateway node")
        print(f"[{self.gateway_id}] Listening on port {self.listen_port}")
        print(f"[{self.gateway_id}] Forwarding to {self.display_ip}:{self.display_port}")
        
        while self.running:
            try:
                data, addr = self.recv_sock.recvfrom(4096)
                self.process_sensor_data(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[{self.gateway_id}] Receive error: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SADRN Gateway Node')
    parser.add_argument('gateway_id', help='Gateway ID (e.g., gw_a, gw_b, gw_c)')
    parser.add_argument('display_ip', help='Display server IP address')
    parser.add_argument('--listen-port', type=int, default=9000, help='Port to listen for sensors')
    parser.add_argument('--display-port', type=int, default=9001, help='Display server port')
    
    args = parser.parse_args()
    
    gateway = GatewayNode(
        gateway_id=args.gateway_id,
        listen_port=args.listen_port,
        display_ip=args.display_ip,
        display_port=args.display_port
    )
    
    gateway.run()
