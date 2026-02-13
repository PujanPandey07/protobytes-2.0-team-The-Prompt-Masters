#!/usr/bin/env python3
"""
SADRN Sensor Node - Runs on Mininet hosts
Generates realistic sensor data and sends to gateway via UDP
Demonstrates actual packet flow through SDN network
"""

import socket
import json
import time
import random
import argparse
import signal
import sys

class SensorNode:
    def __init__(self, sensor_id, sensor_type, gateway_ip, gateway_port=9000, 
                 dashboard_port=5000, min_val=0, max_val=100, threshold=70, unit=''):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.dashboard_port = dashboard_port
        self.min_val = min_val
        self.max_val = max_val
        self.threshold = threshold
        self.unit = unit
        self.current_value = min_val + (max_val - min_val) * 0.3
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1.0)
        
        # Simulation parameters
        self.drift = 0  # Slow drift in readings
        self.spike_probability = 0.02  # 2% chance of spike
        
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
    
    def stop(self, *args):
        self.running = False
        print(f"[{self.sensor_id}] Shutting down...")
        sys.exit(0)
    
    def generate_value(self):
        """Generate realistic sensor value with drift and occasional spikes"""
        # Add slow drift
        self.drift += random.uniform(-0.5, 0.5)
        self.drift = max(-5, min(5, self.drift))
        
        # Normal variation
        variation = random.gauss(0, (self.max_val - self.min_val) * 0.02)
        
        # Occasional spike (simulating disaster event)
        if random.random() < self.spike_probability:
            spike = random.uniform(0.3, 0.6) * (self.max_val - self.min_val)
            self.current_value += spike
            print(f"[{self.sensor_id}] SPIKE detected! Value: {self.current_value:.2f}")
        
        self.current_value += variation + self.drift * 0.1
        self.current_value = max(self.min_val, min(self.max_val, self.current_value))
        
        return round(self.current_value, 2)
    
    def create_packet(self, value):
        """Create sensor data packet"""
        is_alert = value >= self.threshold
        return {
            'type': 'sensor_data',
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'value': value,
            'unit': self.unit,
            'threshold': self.threshold,
            'is_alert': is_alert,
            'priority': 'emergency' if is_alert else 'normal',
            'timestamp': time.time(),
            'source_ip': self.get_own_ip()
        }
    
    def get_own_ip(self):
        """Get own IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.gateway_ip, 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"
    
    def send_to_gateway(self, packet):
        """Send packet to gateway through SDN network"""
        try:
            data = json.dumps(packet).encode('utf-8')
            self.sock.sendto(data, (self.gateway_ip, self.gateway_port))
            return True
        except Exception as e:
            print(f"[{self.sensor_id}] Failed to send to gateway: {e}")
            return False
    
    def run(self, interval=2.0):
        """Main sensor loop"""
        print(f"[{self.sensor_id}] Starting sensor node")
        print(f"[{self.sensor_id}] Type: {self.sensor_type}, Gateway: {self.gateway_ip}:{self.gateway_port}")
        print(f"[{self.sensor_id}] Range: {self.min_val}-{self.max_val} {self.unit}, Threshold: {self.threshold}")
        
        packet_count = 0
        while self.running:
            value = self.generate_value()
            packet = self.create_packet(value)
            
            if self.send_to_gateway(packet):
                packet_count += 1
                status = "ALERT!" if packet['is_alert'] else "normal"
                print(f"[{self.sensor_id}] Sent #{packet_count}: {value:.2f} {self.unit} ({status})")
            
            time.sleep(interval)


# Sensor configurations for different types
SENSOR_CONFIGS = {
    'flood_water': {'type': 'water_level', 'min': 0, 'max': 10, 'threshold': 7, 'unit': 'm'},
    'flood_rain': {'type': 'rainfall', 'min': 0, 'max': 100, 'threshold': 60, 'unit': 'mm/h'},
    'eq_seismic': {'type': 'seismic', 'min': 0, 'max': 10, 'threshold': 5, 'unit': 'Richter'},
    'eq_tilt': {'type': 'tilt', 'min': 0, 'max': 45, 'threshold': 15, 'unit': 'deg'},
    'fire_temp': {'type': 'temperature', 'min': 0, 'max': 100, 'threshold': 55, 'unit': 'C'},
    'fire_smoke': {'type': 'smoke', 'min': 0, 'max': 1000, 'threshold': 300, 'unit': 'ppm'},
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SADRN Sensor Node')
    parser.add_argument('sensor_id', help='Sensor ID (e.g., flood_water, eq_seismic)')
    parser.add_argument('gateway_ip', help='Gateway IP address')
    parser.add_argument('--port', type=int, default=9000, help='Gateway port')
    parser.add_argument('--interval', type=float, default=2.0, help='Send interval in seconds')
    
    args = parser.parse_args()
    
    if args.sensor_id not in SENSOR_CONFIGS:
        print(f"Unknown sensor: {args.sensor_id}")
        print(f"Available: {list(SENSOR_CONFIGS.keys())}")
        sys.exit(1)
    
    config = SENSOR_CONFIGS[args.sensor_id]
    sensor = SensorNode(
        sensor_id=args.sensor_id,
        sensor_type=config['type'],
        gateway_ip=args.gateway_ip,
        gateway_port=args.port,
        min_val=config['min'],
        max_val=config['max'],
        threshold=config['threshold'],
        unit=config['unit']
    )
    
    sensor.run(interval=args.interval)
