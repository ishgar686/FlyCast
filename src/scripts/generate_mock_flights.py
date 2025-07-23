import requests
import os
import json
import time

API_KEY = "6386533e1924dbac6f249177e73a0278"
API_URL = "http://api.aviationstack.com/v1/flights"
FLIGHT_CODES = [
    "WN673", "WN154", "WN1254", "WN310", "WN856", "WN1902", "WN123", "WN1085",
    "UA2405", "UA456", "DL1544", "DL222", "AA1234", "AA678",
    "AS331", "AS1278", "NK808", "F9223", "B62214", "HA54", "SY301"
]
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mock_flights")

os.makedirs(OUTPUT_DIR, exist_ok=True)

for code in FLIGHT_CODES:
    params = {
        "access_key": API_KEY,
        "flight_iata": code
    }
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", [])
        if data:
            out_path = os.path.join(OUTPUT_DIR, f"{code}.json")
            with open(out_path, "w") as f:
                json.dump(data[0], f, indent=2)
            print(f"✅ Saved {code}.json")
        else:
            print(f"❌ No data for {code}")
    except Exception as e:
        print(f"❌ Error for {code}: {e}")
    time.sleep(1)
