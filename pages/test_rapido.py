# test_rapido.py
# Test rápido del módulo ingecart_video_editor
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

# Añadimos la carpeta pages al path para poder importar
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pages"))

from ingecart_video_editor import make_fading_image_clip, process_video


def _make_test_asset(path: Path, size=(640, 360), color=(22, 185, 120)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color)
    img.save(path)
    return path


def _make_test_video(video_path: Path, duration=1.0, fps=12):
    video_path.parent.mkdir(parents=True, exist_ok=True)
    from moviepy import VideoClip

    def make_frame(t):
        rgba = np.zeros((360, 640, 3), dtype=np.uint8)
        rgba[:, :, 0] = 20
        rgba[:, :, 1] = 20
        rgba[:, :, 2] = 30
        if t < duration / 2:
            rgba[:, :, 1] = 150
        return rgba

    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_fps(fps)
    clip.write_videofile(str(video_path), codec="libx264", audio=False, logger=None)
    clip.close()


print("Test 1: make_fading_image_clip...")
placeholder_image = ROOT / "data" / "test_rapido_placeholder.png"
_make_test_asset(placeholder_image)
opening = make_fading_image_clip(str(placeholder_image), (640, 360), 2.5, fps=30)
print(f"   OK - duration={opening.duration}, fps={opening.fps}")
opening.close()

print("Test 2: process_video...")
videos_dir = ROOT / "data" / "test_rapido_videos"
video_in = videos_dir / "input_test.mp4"
video_out = videos_dir / "test_output.mp4"
_make_test_video(video_in, duration=1.0, fps=12)

out = process_video(
    video_path=str(video_in),
    middle_image_path=str(placeholder_image),
    output_path=str(video_out),
)
print(f"   OK: {out}")
print("\nTest completado con éxito ✅")
