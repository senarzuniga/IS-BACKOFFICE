"""Panel de Streamlit para transcripción de audio y generación de resúmenes.

Soporta subir varios archivos de audio (misma sesión), transcribirlos via OpenAI
Whisper (si `OPENAI_API_KEY` está configurada) y generar resúmenes jerárquicos
usando el LLM via `agents.competitive_intelligence.base_agent.BaseAgent`.

El panel ofrece:
- Carga múltiple de archivos de audio
- Campo "Tema/Sesión" para agrupar audios
- Botón para transcribir y opcionalmente generar resumen corto/medio/largo
- Descarga de transcripción consolidada y del resumen (.md / .txt)
"""

from __future__ import annotations

import os
import io
import tempfile
import time
from typing import List, Tuple

import requests
import streamlit as st

from agents.competitive_intelligence.base_agent import BaseAgent


def transcribe_with_openai(file_bytes: bytes, filename: str, language: str | None = None) -> str:
    """Call OpenAI transcription endpoint (REST) to transcribe audio bytes.

    Returns the transcript text or raises an exception on failure.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": (filename, file_bytes)}
    data = {"model": "whisper-1"}
    if language:
        data["language"] = language

    resp = requests.post(url, headers=headers, files=files, data=data, timeout=180)
    resp.raise_for_status()
    j = resp.json()
    return j.get("text", "")


def chunk_text(text: str, size: int = 6000) -> List[str]:
    chunks = []
    idx = 0
    n = len(text)
    while idx < n:
        chunks.append(text[idx: idx + size])
        idx += size
    return chunks


def summarize_hierarchical(text: str, style: str = "short") -> str:
    """Summarize long text by chunking, summarizing each chunk, then merging.

    style: 'short'|'medium'|'long' controls verbosity.
    """
    agent = BaseAgent()

    # first-level chunk summaries
    chunks = chunk_text(text, size=6000)
    summaries = []
    for c in chunks:
        messages = [
            {"role": "system", "content": "You are a concise summarizer helping to convert transcripts into executive summaries. Do not invent facts."},
            {"role": "user", "content": f"Summarize the following transcript into a {style} summary with 3-6 bullet action items. Transcript:\n\n{c}"},
        ]
        s = agent.call_llm(messages, temperature=0.2, max_tokens=800)
        summaries.append(s)
        time.sleep(0.2)

    if len(summaries) == 1:
        return summaries[0]

    # merge summaries
    merged = "\n\n".join(summaries)
    messages = [
        {"role": "system", "content": "You are a senior consultant producing an executive summary from chunk summaries."},
        {"role": "user", "content": f"Produce a consolidated {style} summary and 3-6 prioritized action items from the following chunk summaries:\n\n{merged}"},
    ]
    final = agent.call_llm(messages, temperature=0.2, max_tokens=800)
    return final


def render_audio_transcription_panel() -> None:
    st.title("🔊 Transcripción de audio y resúmenes")
    st.markdown(
        "Sube uno o varios archivos de audio relacionados con un mismo tema. El panel transcribe cada archivo y puede generar un resumen consolidado." 
    )

    st.divider()

    with st.expander("Instrucciones rápidas", expanded=False):
        st.markdown(
            "- Sube archivos en formatos `mp3,wav,m4a,ogg,flac`.
            - Si tienes `OPENAI_API_KEY`, se usará Whisper (whisper-1) para transcribir.
            - Si no hay clave, la transcripción estará deshabilitada y podrás subir transcripciones manuales.")

    topic = st.text_input("Tema / Sesión (opcional)")
    language = st.selectbox("Idioma (opcional)", ["auto", "es", "en", "pt", "fr"], index=0)
    files = st.file_uploader("Sube uno o varios audios", type=["mp3", "wav", "m4a", "ogg", "flac", "aac"], accept_multiple_files=True)

    cols = st.columns([1, 1, 1])
    with cols[0]:
        do_transcribe = st.button("Transcribir archivos")
    with cols[1]:
        do_merge = st.checkbox("Consolidar transcripciones en un único guion", value=True)
    with cols[2]:
        do_summary = st.selectbox("Generar resumen después de transcribir?", ["No", "Corto", "Medio", "Detallado"], index=1)

    if do_transcribe:
        if not files:
            st.error("Selecciona al menos un archivo para transcribir.")
            st.stop()

        transcripts: List[Tuple[str, str]] = []  # (filename, text)

        progress = st.progress(0)
        total = len(files)
        for i, f in enumerate(files, start=1):
            fname = f.name
            st.info(f"Procesando: {fname}")
            try:
                data = f.read()
                if os.getenv("OPENAI_API_KEY"):
                    with st.spinner(f"Transcribiendo {fname}..."):
                        text = transcribe_with_openai(data, fname, language=(None if language == "auto" else language))
                else:
                    st.warning("OPENAI_API_KEY no configurada: transcripción deshabilitada. Añade una transcripción manual si la tienes.")
                    text = "No disponible (OPENAI_API_KEY missing)"
            except Exception as exc:
                st.error(f"Fallo al transcribir {fname}: {exc}")
                text = f"Error: {exc}"

            transcripts.append((fname, text))
            progress.progress(int(i / total * 100))

        progress.empty()

        # display per-file transcripts
        for fname, text in transcripts:
            with st.expander(f"Transcripción: {fname}", expanded=False):
                st.text_area("", value=text, height=240, key=f"ta_{fname}")

        # consolidated transcript
        if do_merge:
            cons = "\n\n".join([f"--- {n} ---\n{t}" for n, t in transcripts])
            st.header("Guion consolidado")
            st.text_area("Guion consolidado", value=cons, height=320)
            st.download_button("Descargar guion (.txt)", cons, file_name=(topic or "transcripts") + ".txt")

        # summarization
        if do_summary and do_summary != "No":
            style = {"Corto": "short", "Medio": "medium", "Detallado": "long"}[do_summary]
            with st.spinner("Generando resumen..."):
                source_text = cons if do_merge else "\n\n".join([t for _, t in transcripts])
                summary = summarize_hierarchical(source_text, style=style)
            st.header("Resumen generado")
            st.markdown(summary)
            st.download_button("Descargar resumen (.md)", summary, file_name=(topic or "summary") + ".md")

        st.success("Proceso completado.")


if __name__ == "__main__":
    render_audio_transcription_panel()
