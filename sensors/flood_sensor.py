#!/usr/bin/env python3
"""Flood Sensor - Water Level & Rainfall monitoring."""

import sys
import time
import random
import requests
import socket
from datetime import datetime

class FloodSensor:
    def __init__(self, gateway_ip, gateway_port=5001):
        self.sensor_id = f"flood_{socket.gethostname()}"
        self.gateway_url = f"http://{gateway_ip}:{gateway_port}/sensor_data"
        self.running = True
        
    def generate_reading(self):
        # Normal: 0-50cm, Emergency: >80cm
        if random.random() < 0.1:  # 10% chance of emergency
            value = random.uniform(80, 120)
            is_emergency = True
        else:
            value = random.uniform(5, 50)
            is_emergency = False
        return round(value, 2), is_emergency
    
    def run(self):
        print(f"[{self.sensor_id}] Starting flood sensor -> {self.gateway_url}")
        while self.running:
            try:
                value, is_emergency = self.generate_reading()
                data = {
                    "sensor_id": self.sensor_id,
                    "sensor_type": "water_level",
                    "value": value,
                    "unit": "cm",
                    "is_emergency": is_emergency,
                    "timestamp": datetime.now().isoformat()
                }
                status = "ALERT!" if is_emergency else "OK"
                print(f"[{self.sensor_id}] {value} cm - {status}")
                
                try:
                    requests.post(self.gateway_url, json=data, timeout=2)
                except:
                    pass
                    
                time.sleep(3)
            except KeyboardInterrupt:
                break
        print(f"[{self.sensor_id}] Stopped")

if __name__ == '__main__':
    gateway_ip = sys.argv[1] if len(sys.argv) > 1 else "10.0.0.1"
    sensor = FloodSensor(gateway_ip)
    sensor.run()
