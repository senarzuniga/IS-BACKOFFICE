import sys
import urllib.request
import traceback

if len(sys.argv) < 2:
    print('Usage: check_streamlit_port.py <port>')
    sys.exit(2)
port = int(sys.argv[1])
url = f'http://127.0.0.1:{port}'
try:
    with urllib.request.urlopen(url, timeout=6) as r:
        print('HTTP', r.getcode())
        data = r.read(512).decode('utf-8', errors='replace')
        print(data[:512])
except Exception as e:
    traceback.print_exc()
    print('ERR', e)
    sys.exit(2)
