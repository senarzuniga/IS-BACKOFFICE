import time
import requests
import sys

url = "http://localhost:8511"
for i in range(60):
    try:
        r = requests.get(url, timeout=5)
        print("STATUS", r.status_code)
        print(r.text[:1200])
        sys.exit(0)
    except Exception as e:
        print(f"Attempt {i+1}: {e}")
        time.sleep(1)
print("FAILED to reach server at", url)
sys.exit(2)
