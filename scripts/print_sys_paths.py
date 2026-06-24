import sys
import json
print(json.dumps(sys.path[:10], indent=2))
