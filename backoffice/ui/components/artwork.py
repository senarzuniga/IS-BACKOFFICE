from __future__ import annotations

from datetime import datetime
import base64
import mimetypes
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont
import streamlit as st


ARTWORK_OUTPUT_DIR = Path(r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\ARTWORK")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def _list_images_in_folder(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        return []
    return sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda p: p.name.lower(),
    )


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_candidates: Iterable[str] = (
        "C:/Windows/Fonts/Inter-Bold.ttf" if bold else "C:/Windows/Fonts/Inter-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    )
    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _crop_cover(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
    src_w, src_h = image.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        new_h = src_h
        new_w = int(new_h * target_ratio)
        left = (src_w - new_w) // 2
        top = 0
    else:
        new_w = src_w
        new_h = int(new_w / target_ratio)
        left = 0
        top = (src_h - new_h) // 2
    cropped = image.crop((left, top, left + new_w, top + new_h))
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def _contain_fit(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    src_w, src_h = image.size
    scale = min(max_w / src_w, max_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    return image.resize((new_w, new_h), Image.Resampling.LANCZOS)


def _image_to_data_uri(source_image: Path) -> str:
    mime_type, _ = mimetypes.guess_type(source_image.name)
    if not mime_type:
        mime_type = "image/png"
    encoded = base64.b64encode(source_image.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _build_html_template(source_image: Path) -> str:
    source_uri = _image_to_data_uri(source_image)
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
<title>Ingecart Industrial Brochure Layout</title>
<link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap\" rel=\"stylesheet\">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#dcdcdc;font-family:'Inter',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:30px;}}
.catalog{{width:1600px;height:900px;background:#ffffff;position:relative;overflow:hidden;border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,0.18);}}
.photo-side{{position:absolute;right:0;top:0;width:58%;height:100%;overflow:hidden;}}
.photo-side img{{width:100%;height:100%;object-fit:cover;object-position:center;filter:brightness(1.02) contrast(1.05) saturate(0.92);}}
.photo-side::before{{content:'';position:absolute;left:-1px;top:0;width:45%;height:100%;background:linear-gradient(to right,rgba(255,255,255,1) 0%,rgba(255,255,255,0.97) 15%,rgba(255,255,255,0.85) 35%,rgba(255,255,255,0.45) 65%,rgba(255,255,255,0) 100%);z-index:2;}}
.photo-side::after{{content:'';position:absolute;inset:0;background:radial-gradient(circle at 20% 50%, rgba(255,255,255,0.25), transparent 40%);z-index:1;}}
.content{{position:relative;z-index:5;width:48%;height:100%;padding:52px 56px;display:flex;flex-direction:column;}}
.kicker{{display:inline-block;background:#f26522;color:#ffffff;font-weight:700;font-size:16px;letter-spacing:.6px;padding:10px 16px;border-radius:999px;margin-bottom:26px;}}
.title{{font-size:56px;line-height:1.02;font-weight:800;color:#121212;max-width:720px;letter-spacing:-1.2px;}}
.title .accent{{color:#f26522;}}
.subtitle{{margin-top:22px;font-size:21px;line-height:1.35;color:#2d2d2d;font-weight:500;max-width:660px;}}
.meta{{margin-top:auto;font-size:14px;letter-spacing:.8px;color:#5f6670;text-transform:uppercase;font-weight:600;}}
.photo-side .photo-wrap{{position:absolute;right:0;top:0;bottom:0;left:0;display:flex;justify-content:flex-end;align-items:center;padding-right:44px;z-index:3;}}
.photo-side .photo-wrap{{position:absolute;right:0;top:0;bottom:0;left:0;display:flex;justify-content:flex-end;align-items:center;padding-right:44px;z-index:3;}}
.photo-side .photo-wrap .photo-img{{position:absolute;right:44px;top:50%;transform:translateY(-50%);width:auto;height:auto;max-width:104%;max-height:94%;object-fit:contain;object-position:right center;}}
.photo-side .photo-wrap .photo-soft{{filter:brightness(1.02) contrast(1.02) saturate(0.94) blur(1.6px);opacity:0.62;}}
.photo-side .photo-wrap .photo-sharp{{filter:brightness(1.05) contrast(1.06) saturate(0.98);
    -webkit-mask-image:linear-gradient(to right,
        rgba(0,0,0,0.00) 0%,
        rgba(0,0,0,0.08) 34%,
        rgba(0,0,0,0.42) 50%,
        rgba(0,0,0,0.78) 64%,
        rgba(0,0,0,1.00) 78%);
    mask-image:linear-gradient(to right,
        rgba(0,0,0,0.00) 0%,
        rgba(0,0,0,0.08) 34%,
        rgba(0,0,0,0.42) 50%,
        rgba(0,0,0,0.78) 64%,
        rgba(0,0,0,1.00) 78%);
}}
.left-fade{{position:absolute;left:0;top:0;width:100%;height:100%;background:linear-gradient(to right, rgba(255,255,255,1) 0%, rgba(255,255,255,0.99) 38%, rgba(255,255,255,0.92) 50%, rgba(255,255,255,0.60) 68%, rgba(255,255,255,0.00) 100%);z-index:2;}}
.soft-texture{{position:absolute;inset:0;background:radial-gradient(circle at 18% 28%, rgba(255,255,255,0.38), transparent 36%), radial-gradient(circle at 12% 72%, rgba(242,101,34,0.045), transparent 26%);z-index:1;}}
.content-fade{{position:absolute;inset:0;background:linear-gradient(to right, rgba(255,255,255,1) 0%, rgba(255,255,255,0.90) 70%, rgba(255,255,255,0) 100%);z-index:1;}}
.top-glow{{position:absolute;top:-120px;left:-120px;width:500px;height:500px;background:radial-gradient(circle,rgba(255,255,255,0.85),transparent 70%);z-index:0;}}
</style>
</head>
<body>
<div class=\"catalog\">
  <div class=\"top-glow\"></div>
        <div class="content">
            <div class="kicker">INGECART AUTOMATION</div>
            <div class="title">Sistema de <span class="accent">carga automatica</span> para camiones</div>
            <div class="subtitle">Solucion industrial para flujo continuo, seguridad operativa y mayor productividad en expedicion.</div>
            <div class="meta">Industrial machinery · installation · robotics · turnkey solutions</div>
        </div>
    <div class=\"photo-side\">
                <div class=\"left-fade\"></div>
                <div class=\"soft-texture\"></div>
                                <div class="photo-wrap">
                                    <img class="photo-img photo-soft" src="{source_uri}" alt="Industrial Photo">
                                    <img class="photo-img photo-sharp" src="{source_uri}" alt="Industrial Photo">
                                </div>
    </div>
    <div class=\"content-fade\"></div>
</div>
</body>
</html>
"""


def _render_with_playwright(html: str, output_png: Path) -> tuple[bool, str]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False, "Playwright is not available in this environment."

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1700, "height": 1000})
            page.set_content(html, wait_until="networkidle")
            page.locator(".catalog").screenshot(path=str(output_png))
            browser.close()
        return True, "Rendered with Playwright HTML engine."
    except Exception as exc:
        return False, f"Playwright rendering error: {exc}"


def _render_with_pillow(source_image: Path, output_png: Path) -> None:
    canvas_w, canvas_h = 1600, 900
    content_w = int(canvas_w * 0.48)
    photo_w = int(canvas_w * 0.58)
    photo_x = canvas_w - photo_w

    base = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    src = Image.open(source_image).convert("RGB")
    # Keep the source image fully visible; do not crop it.
    max_photo_w = int(photo_w * 0.92)
    max_photo_h = int(canvas_h * 0.84)
    photo = _contain_fit(src, max_photo_w, max_photo_h)
    photo_x_offset = photo_x + max(0, (photo_w - photo.width) // 2)
    photo_y_offset = max(0, (canvas_h - photo.height) // 2)

    # Progressive transparency from left to right so image gains definition after center.
    photo_rgba = photo.convert("RGBA")
    alpha_mask = Image.new("L", (photo.width, photo.height), 0)
    mask_px = alpha_mask.load()
    start = int(photo.width * 0.34)
    end = int(photo.width * 0.78)
    span = max(1, end - start)
    for x in range(photo.width):
        if x <= start:
            a = 0
        elif x >= end:
            a = 255
        else:
            a = int(255 * ((x - start) / span))
        for y in range(photo.height):
            mask_px[x, y] = a
    photo_rgba.putalpha(alpha_mask)
    base.alpha_composite(photo_rgba, (photo_x_offset, photo_y_offset))

    # White fade from the left edge of the photo section.
    fade_w = int(photo_w * 0.45)
    fade = Image.new("RGBA", (fade_w, canvas_h), (255, 255, 255, 0))
    fade_px = fade.load()
    for x in range(fade_w):
        alpha = int(255 * max(0.0, 1.0 - (x / fade_w) ** 1.7))
        for y in range(canvas_h):
            fade_px[x, y] = (255, 255, 255, alpha)
    base.paste(fade, (photo_x, 0), fade)

    # Add a softer white industrial background on the left and a blending band.
    left_overlay = Image.new("RGBA", (content_w, canvas_h), (255, 255, 255, 0))
    left_px = left_overlay.load()
    for x in range(content_w):
        alpha = int(255 * (1 - (x / content_w) ** 1.7))
        for y in range(canvas_h):
            left_px[x, y] = (255, 255, 255, min(255, alpha + 18))
    base.paste(left_overlay, (0, 0), left_overlay)

    draw = ImageDraw.Draw(base)

    # Gentle left glow to maintain the same tonal white industrial feel.
    glow = Image.new("RGBA", (520, 520), (255, 255, 255, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r in range(250, 0, -1):
        alpha = int(130 * (r / 250) ** 2)
        glow_draw.ellipse((260 - r, 260 - r, 260 + r, 260 + r), fill=(255, 255, 255, alpha))
    base.paste(glow, (-120, -120), glow)

    base.convert("RGB").save(output_png, format="PNG")


def _generate_artwork(source_image: Path, output_basename: str) -> tuple[Path, Path, str]:
    ARTWORK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in output_basename if c.isalnum() or c in ("-", "_", " ")).strip().replace(" ", "_")
    if not safe_name:
        safe_name = datetime.now().strftime("ingecart_artwork_%Y%m%d_%H%M%S")

    output_png = ARTWORK_OUTPUT_DIR / f"{safe_name}.png"
    output_html = ARTWORK_OUTPUT_DIR / f"{safe_name}.html"

    html = _build_html_template(source_image)
    output_html.write_text(html, encoding="utf-8")

    ok, msg = _render_with_playwright(html, output_png)
    if ok:
        return output_png, output_html, msg

    _render_with_pillow(source_image, output_png)
    return output_png, output_html, f"{msg} Fallback renderer used: Pillow."


def render_ingecart_artwork_block() -> None:
    st.markdown("### INGECART ARTWORK")
    st.caption("Generador visual para creatividades de marketing con layout industrial estilo brochure.")

    source_path_raw = st.text_input(
        "Ruta dinamica de imagen (archivo o carpeta)",
        placeholder=r"C:\Users\Inaki Senar\Pictures\industrial\photo.jpg o carpeta",
        key="artwork_source_path",
    )
    output_name = st.text_input(
        "Nombre del archivo de salida (sin extension)",
        value=f"ingecart_artwork_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        key="artwork_output_name",
    )

    selected_image: Path | None = None
    if source_path_raw:
        source_path = Path(source_path_raw.strip())
        if source_path.exists() and source_path.is_file() and source_path.suffix.lower() in IMAGE_EXTENSIONS:
            selected_image = source_path
            st.success(f"Imagen seleccionada: {selected_image}")
        elif source_path.exists() and source_path.is_dir():
            images = _list_images_in_folder(source_path)
            if images:
                choice = st.selectbox("Selecciona imagen dentro de la carpeta", [str(p) for p in images], key="artwork_image_choice")
                selected_image = Path(choice)
                st.info(f"Carpeta detectada con {len(images)} imagen(es).")
            else:
                st.warning("La carpeta no contiene imagenes compatibles.")
        else:
            st.warning("La ruta indicada no existe o no es valida.")

    st.code(str(ARTWORK_OUTPUT_DIR), language="text")
    generate = st.button("Generar INGECART ARTWORK", type="primary", use_container_width=True, key="artwork_generate")

    if generate:
        if selected_image is None:
            st.error("Debes indicar una imagen valida (archivo o carpeta con imagenes).")
            return

        with st.spinner("Generando artwork..."):
            output_png, output_html, render_message = _generate_artwork(selected_image, output_name)

        st.success("Artwork generado correctamente.")
        st.caption(render_message)
        st.write(f"PNG: {output_png}")
        st.write(f"HTML: {output_html}")
        st.image(str(output_png), caption=output_png.name, use_container_width=True)
