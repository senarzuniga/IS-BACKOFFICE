"""Streamlit panel to manage uploads of videos and documents.

Creates `assets/...` and `public/...` copies with slugified filenames
and can append a simple card to `public/.../index.html`.
"""
from __future__ import annotations

import re
import unicodedata
import html
from pathlib import Path
from typing import Tuple

import streamlit as st


def _slugify(text: str) -> str:
    text = str(text)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^a-z0-9\-\.]", "", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _ensure_dirs(kind: str) -> Tuple[Path, Path]:
    assets = Path("assets") / kind
    public = Path("public") / kind
    assets.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)
    return assets, public


def _build_card_snippet(filename: str, title: str, desc: str, kind: str) -> str:
    # Simple, safe HTML snippet to insert into an index.html
    if kind == "videos":
        return (
            f"<div class=\"card\">\n"
            f"  <video controls preload=\"metadata\" width=\"100%\">\n"
            f"    <source src=\"{html.escape(filename)}\" type=\"video/mp4\">\n"
            f"    Tu navegador no soporta video.\n"
            f"  </video>\n"
            f"  <h3 class=\"card-title\">{html.escape(title)}</h3>\n"
            f"  <p class=\"card-desc\">{html.escape(desc)}</p>\n"
            f"  <a class=\"download-btn\" href=\"{html.escape(filename)}\" download>Descargar</a>\n"
            f"</div>\n"
        )
    # documents
    return (
        f"<div class=\"card\">\n"
        f"  <h3 class=\"card-title\">{html.escape(title)}</h3>\n"
        f"  <p class=\"card-desc\">{html.escape(desc)}</p>\n"
        f"  <a class=\"download-btn\" href=\"{html.escape(filename)}\" target=\"_blank\">Abrir</a>\n"
        f"  <a class=\"download-btn\" href=\"{html.escape(filename)}\" download>Descargar</a>\n"
        f"</div>\n"
    )


def _append_card_to_index(public_dir: Path, snippet: str) -> None:
    index = public_dir / "index.html"
    if not index.exists():
        template = (
            "<!doctype html>\n<html>\n<head><meta charset=\"utf-8\"><title>Media</title></head>\n<body>\n"
            "<div class=\"cards\">\n"
            f"{snippet}\n"
            "</div>\n</body>\n</html>\n"
        )
        index.write_text(template, encoding="utf-8")
        return

    content = index.read_text(encoding="utf-8")
    if "</body>" in content:
        content = content.replace("</body>", f"{snippet}\n</body>")
    else:
        content = content + "\n" + snippet
    index.write_text(content, encoding="utf-8")


def render_media_upload_panel() -> None:
    st.title("📹 Medios — Subir videos y documentos")
    st.markdown(
        "Panel para gestionar subidas locales: renombrado (slug), copia en `assets/` y copia pública en `public/`"
    )

    st.divider()

    with st.expander("Instrucciones rápidas", expanded=False):
        st.markdown(
            "- Prepara el archivo renombrándolo web-friendly (minúsculas, guiones, sin acentos).\n"
            "- Guarda el original en `assets/...` y la copia pública en `public/...`.\n"
            "- Opcional: usar Git LFS para mp4 grandes (`git lfs track "*.mp4"`).\n"
            "- Edita `public/.../index.html` para añadir una tarjeta; el panel puede insertar una tarjeta simple automáticamente."
        )

    kind = st.selectbox("Tipo", ["Videos", "Documentos"], index=0)
    kind_key = "videos" if kind == "Videos" else "docs"

    accepted = {
        "videos": ["mp4", "mov", "avi", "mkv"],
        "docs": ["pdf", "docx", "pptx"],
    }

    files = st.file_uploader(
        f"Selecciona archivo(s) ({', '.join(accepted[kind_key])})",
        type=accepted[kind_key],
        accept_multiple_files=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Título (opcional)")
    with col2:
        description = st.text_input("Descripción corta (opcional)")

    copy_public = st.checkbox(f"Crear copia pública en public/{kind_key}", value=True)
    auto_card = st.checkbox("Añadir tarjeta en public/.../index.html (automático)", value=False)

    st.caption("Se guardarán los originales en `assets/{}` y las copias públicas en `public/{}`".format(kind_key, kind_key))

    if st.button("Subir y procesar"):
        if not files:
            st.error("Selecciona al menos un archivo para subir.")
            st.stop()

        assets_dir, public_dir = _ensure_dirs(kind_key)

        for uploaded in files:
            orig_name = uploaded.name
            stem = Path(orig_name).stem
            ext = Path(orig_name).suffix.lower()
            slug_base = _slugify(stem)
            slug_name = slug_base + ext

            # avoid collisions
            counter = 1
            while (assets_dir / slug_name).exists() or (public_dir / slug_name).exists():
                slug_name = f"{slug_base}-{counter}{ext}"
                counter += 1

            data = uploaded.read()
            (assets_dir / slug_name).write_bytes(data)
            if copy_public:
                (public_dir / slug_name).write_bytes(data)

            st.success(f"{orig_name} → `{slug_name}`")
            if kind_key == "videos" and copy_public:
                try:
                    st.video(str(public_dir / slug_name))
                except Exception:
                    st.info("Video subido. Usa la URL pública para probar reproducción en navegador.")
            elif kind_key == "docs" and copy_public:
                rel = (public_dir / slug_name).as_posix()
                st.markdown(f"[Abrir documento]({rel})")

            if auto_card and copy_public:
                snippet = _build_card_snippet(slug_name, title or stem, description or "", kind_key)
                _append_card_to_index(public_dir, snippet)
                st.info("Tarjeta añadida a public/{}/index.html".format(kind_key))

        st.info("Recuerda: luego `git add assets/ public/` y `git commit` + `git push` para publicar los cambios.")
