import urllib.request
import sys

url = "http://127.0.0.1:8501"
try:
    with urllib.request.urlopen(url, timeout=6) as r:
        print('HTTP', r.getcode())
        data = r.read(512).decode('utf-8', errors='replace')
        print(data[:512])
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERR', e)
    sys.exit(2)
