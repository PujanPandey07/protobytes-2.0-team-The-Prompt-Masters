#!/usr/bin/env python3
"""Fire Sensor - Temperature & Smoke monitoring."""

import sys, time, random, requests, socket
from datetime import datetime

class FireSensor:
    def __init__(self, gateway_ip, gateway_port=5003):
        self.sensor_id = f"fire_{socket.gethostname()}"
        self.gateway_url = f"http://{gateway_ip}:{gateway_port}/sensor_data"
        
    def generate_reading(self):
        # Normal: 20-40°C, Emergency: >70°C
        if random.random() < 0.1:
            value = random.uniform(70, 150)
            is_emergency = True
        else:
            value = random.uniform(20, 40)
            is_emergency = False
        return round(value, 2), is_emergency
    
    def run(self):
        print(f"[{self.sensor_id}] Starting fire sensor -> {self.gateway_url}")
        while True:
            try:
                value, is_emergency = self.generate_reading()
                data = {
                    "sensor_id": self.sensor_id,
                    "sensor_type": "temperature",
                    "value": value,
                    "unit": "°C",
                    "is_emergency": is_emergency,
                    "timestamp": datetime.now().isoformat()
                }
                status = "ALERT!" if is_emergency else "OK"
                print(f"[{self.sensor_id}] {value} °C - {status}")
                try:
                    requests.post(self.gateway_url, json=data, timeout=2)
                except:
                    pass
                time.sleep(3)
            except KeyboardInterrupt:
                break

if __name__ == '__main__':
    gateway_ip = sys.argv[1] if len(sys.argv) > 1 else "10.0.0.3"
    FireSensor(gateway_ip).run()
