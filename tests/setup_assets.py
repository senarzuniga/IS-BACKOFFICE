import base64
from pathlib import Path

# Small 1x1 PNG placeholder (base64)
png_b64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

out = Path("assets/images/smart_plant_overview.png")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(base64.b64decode(png_b64))
print("WROTE", out.resolve())
