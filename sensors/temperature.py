#!/usr/bin/env python3
"""SADRN Temperature Sensor - Fire monitoring (Gateway C)"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sensors.sensor_base import SensorBase, parse_args

class TemperatureSensor(SensorBase):
    def __init__(self, gateway_ip, gateway_port):
        super().__init__(
            sensor_id="TEMPERATURE_01",
            sensor_type="temperature",
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            interval=3.0,
            spike_probability=0.15
        )
    
    def get_normal_range(self):
        return (20, 35)
    
    def get_emergency_threshold(self):
        return 60
    
    def get_unit(self):
        return "C"

def main():
    gateway_ip, gateway_port = parse_args()
    if len(sys.argv) < 2:
        gateway_ip = "10.0.3.1"
        gateway_port = 5003
    sensor = TemperatureSensor(gateway_ip, gateway_port)
    sensor.run()

if __name__ == '__main__':
    main()
