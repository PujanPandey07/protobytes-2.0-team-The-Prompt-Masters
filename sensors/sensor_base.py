#!/usr/bin/env python3
"""
SADRN Sensor Base Class

This module provides the base class for all disaster monitoring sensors.
Each sensor generates simulated data and sends it to its gateway via HTTP POST.
"""

import time
import random
import json
import requests
import signal
import sys
from abc import ABC, abstractmethod
from datetime import datetime


class SensorBase(ABC):
    """
    Abstract base class for all SADRN sensors.
    """
    
    def __init__(self, sensor_id, sensor_type, gateway_ip, gateway_port,
                 interval=3.0, spike_probability=0.15):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.interval = interval
        self.spike_probability = spike_probability
        self.running = True
        self.consecutive_emergencies = 0
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n[{self.sensor_id}] Shutting down...")
        self.running = False
    
    @abstractmethod
    def get_normal_range(self):
        pass
    
    @abstractmethod
    def get_emergency_threshold(self):
        pass
    
    @abstractmethod
    def get_unit(self):
        pass
    
    def generate_reading(self):
        min_val, max_val = self.get_normal_range()
        emergency_threshold = self.get_emergency_threshold()
        
        if random.random() < self.spike_probability:
            value = random.uniform(emergency_threshold, emergency_threshold * 1.5)
            is_emergency = True
            self.consecutive_emergencies += 1
        else:
            value = random.uniform(min_val, max_val)
            is_emergency = False
            self.consecutive_emergencies = 0
        
        return round(value, 2), is_emergency
    
    def create_data_packet(self, value, is_emergency):
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "value": value,
            "unit": self.get_unit(),
            "is_emergency": is_emergency,
            "consecutive_emergencies": self.consecutive_emergencies,
            "timestamp": datetime.now().isoformat(),
            "threshold": self.get_emergency_threshold()
        }
    
    def send_to_gateway(self, data):
        url = f"http://{self.gateway_ip}:{self.gateway_port}/sensor_data"
        
        try:
            response = requests.post(url, json=data, timeout=5)
            if response.status_code == 200:
                return True
            else:
                print(f"[{self.sensor_id}] Gateway returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"[{self.sensor_id}] Cannot connect to gateway at {url}")
            return False
        except requests.exceptions.Timeout:
            print(f"[{self.sensor_id}] Timeout connecting to gateway")
            return False
        except Exception as e:
            print(f"[{self.sensor_id}] Error sending data: {e}")
            return False
    
    def run(self):
        print(f"[{self.sensor_id}] Starting {self.sensor_type} sensor")
        print(f"[{self.sensor_id}] Gateway: {self.gateway_ip}:{self.gateway_port}")
        print(f"[{self.sensor_id}] Interval: {self.interval}s, Spike probability: {self.spike_probability*100}%")
        print(f"[{self.sensor_id}] Normal range: {self.get_normal_range()} {self.get_unit()}")
        print(f"[{self.sensor_id}] Emergency threshold: {self.get_emergency_threshold()} {self.get_unit()}")
        print("-" * 60)
        
        while self.running:
            try:
                value, is_emergency = self.generate_reading()
                data = self.create_data_packet(value, is_emergency)
                status = "EMERGENCY" if is_emergency else "Normal"
                print(f"[{self.sensor_id}] {value} {self.get_unit()} - {status}")
                success = self.send_to_gateway(data)
                if not success:
                    print(f"[{self.sensor_id}] Failed to send - will retry next cycle")
                time.sleep(self.interval)
            except Exception as e:
                print(f"[{self.sensor_id}] Error in main loop: {e}")
                time.sleep(self.interval)
        
        print(f"[{self.sensor_id}] Sensor stopped")


def parse_args():
    gateway_ip = "10.0.1.1"
    gateway_port = 5001
    
    if len(sys.argv) >= 2:
        gateway_ip = sys.argv[1]
    if len(sys.argv) >= 3:
        gateway_port = int(sys.argv[2])
    
    return gateway_ip, gateway_port
