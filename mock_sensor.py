# mock_sensor/mock_sensor.py
import random
import time
import requests
import json
from datetime import datetime

API_URL = "https://cold-chain-monitor.replit.app/api/data"  # change if needed
DEVICE_ID = "simulated_coldchain_01"
SEND_INTERVAL = 10

def fake_temperature():
    return round(random.uniform(-5, 10), 2)

def fake_humidity():
    return round(random.uniform(60, 95), 2)

def fake_battery():
    return round(random.uniform(3.3, 4.2), 2)

def fake_door():
    return "open" if random.random() < 0.05 else "closed"

def main():
    print("Mock sensor started, sending to", API_URL)
    while True:
        data = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "temperature_c": fake_temperature(),
            "humidity_percent": fake_humidity(),
            "battery_voltage": fake_battery(),
            "door_state": fake_door()
        }
        try:
            res = requests.post(API_URL, json=data, timeout=5)
            print("Sent:", data, "Response:", res.status_code, res.text)
        except Exception as e:
            print("Send error:", e)
        time.sleep(SEND_INTERVAL)

if __name__ == "__main__":
    main()
