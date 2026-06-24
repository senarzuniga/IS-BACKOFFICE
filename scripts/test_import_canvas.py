import sys
import pathlib
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
_candidates = [
    ROOT / "ingecart-marketing-kit",
    ROOT / "informes" / "ingecart-marketing-kit" / "ingecart-marketing-kit",
    ROOT / "informes" / "ingecart-marketing-kit",
]
for p in _candidates:
    try:
        if p.exists():
            # prefer marketing kit path first
            sys.path.insert(0, str(p))
            break
    except Exception:
        continue

# Ensure project root is available
if str(ROOT) not in sys.path:
    if any(str(x) in sys.path for x in _candidates if x.exists()):
        sys.path.insert(1, str(ROOT))
    else:
        sys.path.insert(0, str(ROOT))

print('sys.path[0:3]=', sys.path[:3])

try:
    from plant_simulator.canvas_builder import build_canvas_html
    print('IMPORT_OK: build_canvas_html found')
except Exception as e:
    print('IMPORT_ERR')
    traceback.print_exc()
    print(e)
