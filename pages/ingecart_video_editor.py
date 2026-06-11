"""
Ingecart Video Editor
======================
Panel para editar videos añadiendo:
  - Imagen de inicio (con fade-in de 90% -> 0% de transparencia en 2.5s)
  - Imagen intermedia seleccionable (con fade-in de 90% -> 0% en 2s)
  - Video original
  - Imagen de cierre (con fade-in de 90% -> 0% en 2s)

Los videos editados se guardan en:
  C:\\Users\\Inaki Senar\\Documents\\INGECART\\MARKETING\\ARTWORK\\VIDEOS
"""

import os
import tempfile
import traceback
from pathlib import Path

import streamlit as st
import numpy as np
from PIL import Image

# MoviePy 2.x
from moviepy import (
    VideoFileClip,
    VideoClip,
    concatenate_videoclips,
)


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================
BASE_DIR = Path(r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING")
OPENING_IMAGE_PATH = BASE_DIR / "ARTWORK" / "Imagen Slogan principal Ingecart 1.png"
CLOSING_IMAGE_PATH = BASE_DIR / "LOGOS" / "ICON ORANGE.png"
OUTPUT_DIR = BASE_DIR / "ARTWORK" / "VIDEOS"

# Crear el directorio de salida si no existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Parámetros de los fades
OPENING_FADE_DURATION = 2.5     # segundos (imagen de inicio)
MIDDLE_FADE_DURATION = 2.0      # segundos (imagen intermedia, seleccionable)
CLOSING_FADE_DURATION = 2.0     # segundos (imagen de cierre)
INITIAL_OPACITY = 0.10          # 10% de visibilidad (90% de transparencia)
FINAL_OPACITY = 1.0             # 100% de visibilidad (0% de transparencia)


# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Ingecart Video Editor",
    page_icon="🎬",
    layout="wide",
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================
def normalize_image_to_canvas(image_path: str, target_size: tuple) -> np.ndarray:
    """
    Carga una imagen, la redimensiona manteniendo proporción
    para que quepa en el lienzo (target_size) y la centra sobre
    un fondo NEGRO RGB del tamaño exacto del lienzo.
    Devuelve un array numpy RGB uint8 de shape (h, w, 3).
    """
    target_w, target_h = target_size
    img = Image.open(image_path).convert("RGBA")

    # Calcular escala manteniendo proporción
    img_w, img_h = img.size
    scale = min(target_w / img_w, target_h / img_h)
    new_w, new_h = int(img_w * scale), int(img_h * scale)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    # Pegar sobre canvas RGB negro
    canvas = Image.new("RGB", target_size, (0, 0, 0))
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    if img_resized.mode == "RGBA":
        canvas.paste(img_resized, (offset_x, offset_y), mask=img_resized.split()[3])
    else:
        canvas.paste(img_resized, (offset_x, offset_y))

    return np.array(canvas, dtype=np.uint8)


def make_fading_image_clip(
    image_path: str,
    target_size: tuple,
    duration: float,
    fps: int = 30,
) -> VideoClip:
    """
    Crea un clip de video a partir de una imagen estática con la
    opacidad animando desde INITIAL_OPACITY hasta FINAL_OPACITY
    a lo largo de `duration` segundos.

    La opacidad se SIMULA multiplicando los píxeles RGB por el alpha
    (sobre un fondo negro), por lo que el clip resultante es RGB puro
    y se puede concatenar con videos RGB sin problemas.

    Devuelve un VideoClip RGB de tamaño (v_w, v_h).
    """
    # 1) Cargamos la imagen y la normalizamos al tamaño del video destino
    rgb_array = normalize_image_to_canvas(image_path, target_size)
    h, w = rgb_array.shape[:2]
    total_frames = max(1, int(duration * fps))

    # 2) Calculamos los alfas para cada frame
    alphas = np.linspace(INITIAL_OPACITY, FINAL_OPACITY, total_frames)
    alpha_f32 = alphas.astype(np.float32)

    # 3) frame_function: para cada t devolvemos un frame RGB
    #    con los píxeles multiplicados por el alpha (sobre fondo negro)
    def frame_function(t):
        try:
            t_values = np.atleast_1d(np.asarray(t, dtype=float))
            indices = np.clip(
                (t_values * fps).astype(int),
                0,
                total_frames - 1,
            )
            current_alphas = alpha_f32[indices]  # shape (N,)

            # Construir batch (N, h, w, 3) RGB
            n = len(t_values)
            # Empezamos con un fondo negro
            out = np.zeros((n, h, w, 3), dtype=np.float32)
            # Sumamos la imagen multiplicada por el alpha
            img_batch = rgb_array.astype(np.float32)[None, ...]  # (1, h, w, 3)
            out += img_batch * current_alphas[:, None, None, None]
            out = np.clip(out, 0, 255).astype(np.uint8)

            if np.isscalar(t):
                return out[0]
            return out
        except Exception:
            # Fallback seguro
            idx = int(min(max(t * fps, 0), total_frames - 1))
            return (rgb_array.astype(np.float32) * alpha_f32[idx]).clip(0, 255).astype(np.uint8)

    clip = VideoClip(frame_function=frame_function, duration=duration)
    clip = clip.with_fps(fps)
    return clip


def save_uploaded_file(uploaded_file, target_dir: Path) -> Path:
    """
    Guarda un UploadedFile de Streamlit en `target_dir` y
    devuelve la ruta final.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return dest


def process_video(
    video_path: str,
    middle_image_path: str,
    output_path: str,
    opening_image_path: str = str(OPENING_IMAGE_PATH),
    closing_image_path: str = str(CLOSING_IMAGE_PATH),
    fps: int = 30,
) -> str:
    """
    Procesa el video aplicando las 3 imágenes con fade-in de
    opacidad simulada (multiplicativa sobre fondo negro).
    """
    # Abrimos el video original
    with VideoFileClip(video_path) as video:
        v_w, v_h = video.size
        video_fps = video.fps or fps

        # Aseguramos que el video tenga fps par (libx264 lo requiere)
        if abs(video_fps - round(video_fps)) > 0.01:
            video_fps = round(video_fps)
        if video_fps < 1:
            video_fps = fps

        # 1) Imagen de inicio
        opening_clip = make_fading_image_clip(
            opening_image_path,
            (v_w, v_h),
            OPENING_FADE_DURATION,
            fps=int(video_fps),
        )

        # 2) Imagen intermedia seleccionable
        middle_clip = make_fading_image_clip(
            middle_image_path,
            (v_w, v_h),
            MIDDLE_FADE_DURATION,
            fps=int(video_fps),
        )

        # 3) Imagen de cierre
        closing_clip = make_fading_image_clip(
            closing_image_path,
            (v_w, v_h),
            CLOSING_FADE_DURATION,
            fps=int(video_fps),
        )

        # 4) Aseguramos que el video central tenga el mismo fps
        #    y que su audio se preserve al concatenar
        video_for_concat = video.with_fps(int(video_fps))

        # 5) Concatenamos los 4 clips en orden
        #    Como ahora todos son RGB y del mismo tamaño/fps,
        #    method="chain" funciona perfectamente y es más eficiente.
        final = concatenate_videoclips(
            [opening_clip, middle_clip, video_for_concat, closing_clip],
            method="chain",
        )

        # 6) Escribimos el archivo
        final.write_videofile(
            output_path,
            codec="libx264",
            preset="medium",
            fps=int(video_fps),
            audio=True,
            logger=None,
        )

        final.close()
        opening_clip.close()
        middle_clip.close()
        closing_clip.close()
        if video_for_concat is not video:
            try:
                video_for_concat.close()
            except Exception:
                pass

    return output_path


# ============================================================
# UI - STREAMLIT
# ============================================================
st.title("🎬 Ingecart Video Editor")
st.markdown(
    "Sube un video, elige una imagen intermedia, y generamos un video "
    "con **imagen de inicio + imagen intermedia + video + imagen de cierre**, "
    "todas con un fundido de opacidad del 10% al 100% sobre fondo negro."
)

# Sidebar con info
with st.sidebar:
    st.header("⚙️ Configuración")
    st.markdown(
        f"""
        **Imagen de inicio (fija):**  
        `{OPENING_IMAGE_PATH}`
        
        **Imagen de cierre (fija):**  
        `{CLOSING_IMAGE_PATH}`
        
        **Fade inicio:** {OPENING_FADE_DURATION} s  
        **Fade imagen intermedia:** {MIDDLE_FADE_DURATION} s  
        **Fade cierre:** {CLOSING_FADE_DURATION} s  
        **Opacidad inicial:** 10% (90% transparencia)  
        **Opacidad final:** 100% (0% transparencia)
        """
    )

    # Validar que las imágenes fijas existen
    st.divider()
    st.subheader("📁 Estado de las imágenes fijas")
    if OPENING_IMAGE_PATH.exists():
        st.success("✅ Imagen de inicio OK")
    else:
        st.error(f"❌ Falta imagen de inicio:\n{OPENING_IMAGE_PATH}")
    if CLOSING_IMAGE_PATH.exists():
        st.success("✅ Imagen de cierre OK")
    else:
        st.error(f"❌ Falta imagen de cierre:\n{CLOSING_IMAGE_PATH}")


# Selección de video
st.subheader("1️⃣ Sube el video a editar")
video_file = st.file_uploader(
    "Selecciona un video",
    type=["mp4", "mov", "avi", "mkv", "webm"],
    key="video_uploader",
)

if video_file is not None:
    st.session_state["video_name"] = video_file.name
    st.info(f"📹 Video seleccionado: **{video_file.name}**")

# Selección de la imagen intermedia
st.subheader("2️⃣ Elige la imagen intermedia")
middle_option = st.radio(
    "Origen de la imagen intermedia:",
    ("Subir una imagen", "Elegir de la carpeta ARTWORK"),
    horizontal=True,
)

middle_image_path = None

if middle_option == "Subir una imagen":
    middle_file = st.file_uploader(
        "Sube la imagen intermedia",
        type=["png", "jpg", "jpeg", "webp"],
        key="middle_uploader",
    )
    if middle_file is not None:
        middle_image_path = save_uploaded_file(
            middle_file,
            BASE_DIR / "ARTWORK",
        )
        st.success(f"✅ Imagen guardada en: `{middle_image_path}`")
else:
    artwork_dir = BASE_DIR / "ARTWORK"
    if artwork_dir.exists():
        image_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
        available_images = sorted([
            f.name for f in artwork_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_exts
        ])
        if available_images:
            selected = st.selectbox(
                "Selecciona una imagen de ARTWORK:",
                available_images,
            )
            middle_image_path = artwork_dir / selected
            st.image(str(middle_image_path), caption=selected, width=400)
        else:
            st.warning("No se han encontrado imágenes en la carpeta ARTWORK.")
    else:
        st.error(f"No existe la carpeta: {artwork_dir}")

# Configuración de salida
st.subheader("3️⃣ Nombre del archivo de salida")
default_name = ""
if video_file is not None:
    stem = Path(video_file.name).stem
    default_name = f"{stem}_editado.mp4"
output_filename = st.text_input(
    "Nombre del archivo (se guardará en la carpeta VIDEOS):",
    value=default_name,
    help="No es necesario añadir la extensión, se añadirá automáticamente.",
)

# Botón de procesamiento
st.subheader("4️⃣ Generar video")
can_process = (
    video_file is not None
    and middle_image_path is not None
    and Path(middle_image_path).exists()
    and OPENING_IMAGE_PATH.exists()
    and CLOSING_IMAGE_PATH.exists()
    and output_filename.strip() != ""
)

if not can_process:
    st.info("Completa todos los pasos para poder generar el video.")

if st.button("🎬 Generar video editado", disabled=not can_process, type="primary"):
    status = st.status("Procesando video…", expanded=True)

    try:
        status.update(label="Guardando video temporal…")
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(video_file.name).suffix
        ) as tmp_vid:
            tmp_vid.write(video_file.getbuffer())
            tmp_video_path = tmp_vid.name

        if not output_filename.lower().endswith(".mp4"):
            output_filename = output_filename + ".mp4"
        output_path = OUTPUT_DIR / output_filename

        status.update(label="Renderizando video (puede tardar)…")
        final_path = process_video(
            video_path=tmp_video_path,
            middle_image_path=str(middle_image_path),
            output_path=str(output_path),
        )

        status.update(label="✅ Video generado correctamente", state="complete")

        st.success(f"🎉 Video guardado en: `{final_path}`")
        st.video(final_path)

        with open(final_path, "rb") as f:
            st.download_button(
                label="⬇️ Descargar video",
                data=f.read(),
                file_name=output_filename,
                mime="video/mp4",
            )

        try:
            os.unlink(tmp_video_path)
        except OSError:
            pass

    except Exception as e:
        status.update(label="❌ Error durante el procesamiento", state="error")
        st.error(f"Ha ocurrido un error: {e}")
        with st.expander("Ver traceback completo"):
            st.code(traceback.format_exc())


st.divider()
st.caption(
    "Ingecart Video Editor · Panel interno · "
    f"Salida en: `{OUTPUT_DIR}`"
)
