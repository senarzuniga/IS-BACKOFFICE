# test_rapido.py
# Test rápido del módulo ingecart_video_editor
import sys
import os
from pathlib import Path

# Añadimos la carpeta pages al path para poder importar
sys.path.insert(0, r"C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE\pages")

from ingecart_video_editor import make_fading_image_clip, process_video

# 1) Probar que make_fading_image_clip no falla
print("Test 1: make_fading_image_clip...")
opening = make_fading_image_clip(
    r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\ARTWORK\Imagen Slogan principal Ingecart 1.png",
    (640, 360),
    2.5,
    fps=30,
)
print(f"   OK - duration={opening.duration}, fps={opening.fps}")

# 2) Renderizar un video de prueba
print("Test 2: process_video...")
videos_dir = r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\ARTWORK\VIDEOS"

# Busca cualquier video de prueba existente
existing_videos = [
    f for f in os.listdir(videos_dir)
    if f.lower().endswith(('.mp4', '.mov', '.avi'))
]
if not existing_videos:
    print(f"ERROR: no hay videos de prueba en {videos_dir}")
    print("Copia un video pequeño cualquiera a esa carpeta para hacer el test.")
    sys.exit(1)

test_input = os.path.join(videos_dir, existing_videos[0])
test_output = os.path.join(videos_dir, "test_output.mp4")
print(f"   Input:  {test_input}")
print(f"   Output: {test_output}")

out = process_video(
    video_path=test_input,
    middle_image_path=r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\ARTWORK\Imagen Slogan principal Ingecart 1.png",
    output_path=test_output,
)
print(f"   OK: {out}")
print("\nTest completado con éxito ✅")
