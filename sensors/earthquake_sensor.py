#!/usr/bin/env python3
"""Earthquake Sensor - Vibration & Tilt monitoring."""

import sys, time, random, requests, socket
from datetime import datetime

class EarthquakeSensor:
    def __init__(self, gateway_ip, gateway_port=5002):
        self.sensor_id = f"earthquake_{socket.gethostname()}"
        self.gateway_url = f"http://{gateway_ip}:{gateway_port}/sensor_data"
        
    def generate_reading(self):
        # Normal: 0-3 Richter, Emergency: >5
        if random.random() < 0.08:
            value = random.uniform(5.0, 7.5)
            is_emergency = True
        else:
            value = random.uniform(0.1, 3.0)
            is_emergency = False
        return round(value, 2), is_emergency
    
    def run(self):
        print(f"[{self.sensor_id}] Starting earthquake sensor -> {self.gateway_url}")
        while True:
            try:
                value, is_emergency = self.generate_reading()
                data = {
                    "sensor_id": self.sensor_id,
                    "sensor_type": "seismic",
                    "value": value,
                    "unit": "Richter",
                    "is_emergency": is_emergency,
                    "timestamp": datetime.now().isoformat()
                }
                status = "ALERT!" if is_emergency else "OK"
                print(f"[{self.sensor_id}] {value} Richter - {status}")
                try:
                    requests.post(self.gateway_url, json=data, timeout=2)
                except:
                    pass
                time.sleep(3)
            except KeyboardInterrupt:
                break

if __name__ == '__main__':
    gateway_ip = sys.argv[1] if len(sys.argv) > 1 else "10.0.0.2"
    EarthquakeSensor(gateway_ip).run()
