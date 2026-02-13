import socket, json, sys
from datetime import datetime

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    print(f"SADRN Display Server on UDP port {port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    print("Ready to receive sensor data...")
    try:
        while True:
            data_bytes, addr = sock.recvfrom(4096)
            try:
                data = json.loads(data_bytes.decode("utf-8"))
                ts = datetime.now().strftime("%H:%M:%S")
                gw = data.get("gateway_id", "?")
                sensor = data.get("sensor_id", "unknown")
                value = data.get("value", 0)
                unit = data.get("unit", "")
                priority = data.get("priority", "normal")
                is_alert = data.get("is_alert", False) or priority == "emergency"
                tag = "ALARM" if is_alert else "OK"
                print(f"[{ts}] {gw} | {sensor:14} | {value:8.2f} {unit:6} | {priority} [{tag}]")
            except Exception as e:
                print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
