#!/usr/bin/env python3
"""
SADRN - Receiver Script for Display Node (h_display)
Listens for packets from all sensors and provides stats via HTTP
"""

import socket
import json
import time
import threading
import signal
from datetime import datetime
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

NORMAL_PORT = 5000
EMERGENCY_PORT = 5001
HTTP_PORT = 8080
MAX_HISTORY = 1000


class PacketStats:
    def __init__(self):
        self.lock = threading.Lock()
        self.total = self.normal = self.emergency = 0
        self.by_host = {'h1': 0, 'h2': 0, 'h3': 0}
        self.emergency_by_host = {'h1': 0, 'h2': 0, 'h3': 0}
        self.history = deque(maxlen=MAX_HISTORY)
        self.recent = deque(maxlen=50)
        self.latencies = deque(maxlen=1000)
        self.start_time = datetime.now()
    
    def add(self, host_id, is_emergency, timestamp, data):
        with self.lock:
            self.total += 1
            if is_emergency:
                self.emergency += 1
                if host_id in self.emergency_by_host:
                    self.emergency_by_host[host_id] += 1
            else:
                self.normal += 1
            if host_id in self.by_host:
                self.by_host[host_id] += 1
            
            latency = None
            try:
                latency = (datetime.now() - datetime.fromisoformat(timestamp)).total_seconds() * 1000
                self.latencies.append(latency)
            except:
                pass
            
            record = {'id': self.total, 'host_id': host_id, 'priority': 'CRITICAL' if is_emergency else 'NORMAL',
                      'recv_time': datetime.now().isoformat(), 'latency_ms': latency, 'data': data}
            self.history.append(record)
            self.recent.append(record)
    
    def get_stats(self):
        with self.lock:
            uptime = (datetime.now() - self.start_time).total_seconds()
            return {
                'total_packets': self.total, 'normal_packets': self.normal, 'emergency_packets': self.emergency,
                'packets_by_host': dict(self.by_host), 'emergency_by_host': dict(self.emergency_by_host),
                'avg_latency_ms': sum(self.latencies)/len(self.latencies) if self.latencies else None,
                'packets_per_second': self.total / max(1, uptime), 'uptime_seconds': uptime
            }
    
    def get_recent(self, count=20):
        with self.lock:
            return list(self.recent)[-count:]


class DisplayReceiver:
    def __init__(self):
        self.running = True
        self.stats = PacketStats()
        signal.signal(signal.SIGINT, lambda s, f: setattr(self, 'running', False))
        signal.signal(signal.SIGTERM, lambda s, f: setattr(self, 'running', False))
        print("[h_display] Display Node Receiver initialized")
    
    def receive_packets(self, port, is_emergency):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        sock.bind(('', port))
        print(f"[h_display] Listening on {port} ({'EMERGENCY' if is_emergency else 'NORMAL'})")
        
        while self.running:
            try:
                data, addr = sock.recvfrom(4096)
                pkt = json.loads(data.decode('utf-8'))
                self.stats.add(pkt.get('host_id', 'unknown'), is_emergency, pkt.get('timestamp', ''), pkt)
                priority = "\033[91mCRITICAL\033[0m" if is_emergency else "\033[92mNORMAL\033[0m"
                print(f"[h_display] [{priority}] From {pkt.get('host_id', 'unknown')} via {addr[0]}")
            except socket.timeout:
                pass
            except Exception as e:
                if self.running:
                    print(f"[h_display] Error: {e}")
        sock.close()
    
    def run_http(self):
        stats_ref = self.stats
        running_ref = lambda: self.running
        
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                if self.path == '/stats':
                    self.wfile.write(json.dumps(stats_ref.get_stats()).encode())
                elif self.path.startswith('/packets'):
                    self.wfile.write(json.dumps(stats_ref.get_recent(50)).encode())
                elif self.path == '/health':
                    self.wfile.write(json.dumps({'status': 'ok'}).encode())
                else:
                    self.wfile.write(b'{}')
        
        class Server(socketserver.ThreadingMixIn, HTTPServer):
            allow_reuse_address = True
        
        server = Server(('', HTTP_PORT), Handler)
        server.timeout = 1.0
        print(f"[h_display] HTTP on port {HTTP_PORT}")
        while self.running:
            server.handle_request()
        server.server_close()
    
    def run(self):
        print("[h_display] Starting receivers...")
        threads = [
            threading.Thread(target=self.receive_packets, args=(NORMAL_PORT, False), daemon=True),
            threading.Thread(target=self.receive_packets, args=(EMERGENCY_PORT, True), daemon=True),
            threading.Thread(target=self.run_http, daemon=True)
        ]
        for t in threads:
            t.start()
        
        while self.running:
            time.sleep(10)
            s = self.stats.get_stats()
            print(f"\n[STATS] Total: {s['total_packets']} | Normal: {s['normal_packets']} | Emergency: {s['emergency_packets']}\n")
        print("[h_display] Stopped")


if __name__ == '__main__':
    DisplayReceiver().run()
