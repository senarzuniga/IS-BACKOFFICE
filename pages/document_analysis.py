"""Capa 8: Panel Streamlit de Inteligencia Documental Autónoma."""
from __future__ import annotations
import asyncio
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.doc_orchestrator import MultiAgentOrchestrator  # noqa: E402

st.set_page_config(page_title="IS-BACKOFFICE · Inteligencia Documental",
                   page_icon="🧠", layout="wide")

st.markdown("""
<style>
.doc-card { background:#FFFFFF; border:1px solid #E2EAF3;
            border-left:4px solid #3b82f6; border-radius:10px;
            padding:14px 18px; margin-bottom:10px; }
.doc-card-ok  { border-left-color:#10b981; }
.doc-card-warn{ border-left-color:#f59e0b; }
.metric-box { background:#F8FAFC; border-radius:8px; padding:12px; }
</style>
""", unsafe_allow_html=True)


def _init() -> None:
    if "doc_orch" not in st.session_state:
        with st.spinner("🧠 Inicializando memoria corporativa y grafo…"):
            st.session_state.doc_orch = MultiAgentOrchestrator()
    if "doc_history" not in st.session_state:
        st.session_state.doc_history = []


def _sidebar() -> None:
    orch = st.session_state.doc_orch
    with st.sidebar:
        st.markdown("### 🩺 Autochecks del Sistema")
        ms = orch.memory.stats(); gs = orch.graph.stats()
        c1, c2 = st.columns(2)
        c1.metric("Hechos", ms["total_facts"])
        c2.metric("Confianza", f"{ms['avg_confidence']:.2f}")
        c1.metric("Entidades", gs["total_entities"])
        c2.metric("Relaciones", gs["total_relationships"])
        st.markdown("#### 🤖 Agentes")
        st.success("✅ Analista Documental")
        st.success("✅ Investigador Web")
        st.success("✅ Auditor")
        st.markdown("#### 🧠 Multi-LLM")
        st.caption("GPT-4 · Claude · Gemini · Llama")
        if st.button("🧹 Limpiar historial", use_container_width=True):
            st.session_state.doc_history = []; st.rerun()


def _examples() -> None:
    with st.expander("💡 Ejemplos de comandos", expanded=False):
        st.markdown("""
- `Analiza C:\\Clientes\\PCM_Mexico y genera informe ejecutivo comercial`
- `Benchmark sectorial comparando PCM con Cascades y WestRock`
- `Due diligence de C:\\Deals\\Oportunidad con verificación web`
- `Analiza la carpeta del proyecto PSC Visalia y dame entidades clave`
        """)


def _history() -> None:
    h = st.session_state.doc_history
    if not h: return
    with st.expander(f"🗂️ Historial ({len(h)})", expanded=False):
        for i, e in enumerate(reversed(h[-10:]), 1):
            st.markdown(f"**{i}.** {e['cmd'][:80]} — {e['ts']}")


def main() -> None:
    _init()
    _sidebar()
    _history()

    st.title("🧠 Inteligencia Documental Autónoma")
    st.caption("Sistema multiagente con memoria corporativa, grafo y verificación cruzada")
    _examples()

    st.markdown("### 🎯 Comando de alto nivel")
    cmd = st.text_area("Comando", height=110,
        placeholder='Ej: Analiza "C:\\Clientes\\PCM_Mexico" y genera informe ejecutivo',
        label_visibility="collapsed")

    c1, c2 = st.columns([1, 5])
    run = c1.button("▶️ Ejecutar análisis", type="primary", use_container_width=True)
    if c2.button("🧹 Limpiar"): st.session_state.doc_history = []; st.rerun()

    if not (run and cmd.strip()): return

    with st.status("🚀 Orquestando agentes…", expanded=True) as status:
        log = status.container()
        def cb(msg: str): log.markdown(f"- {msg}")
        try:
            result = asyncio.run(st.session_state.doc_orch.execute(cmd, cb))
            status.update(label="✅ Análisis completado", state="complete")
        except Exception as e:
            status.update(label="❌ Error", state="error"); st.error(str(e)); st.exception(e); return

    st.session_state.doc_history.append({"cmd": cmd, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    st.markdown("---")
    st.markdown("## 📊 Resultados del Análisis")

    r = result["results"]; a = r.get("analista", {}); aud = r.get("auditor", {})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Documentos", a.get("documents_processed", 0))
    m2.metric("Entidades", len(a.get("entities", [])))
    m3.metric("Hechos", a.get("facts_extracted", 0))
    m4.metric("Verificación", f"{aud.get('verification_rate', 0)*100:.0f}%")

    ents = a.get("entities", [])
    if ents:
        st.markdown("### 🏷️ Entidades detectadas")
        by_type: dict = {}
        for e in ents: by_type.setdefault(e["type"], []).append(e["value"])
        for t, vs in by_type.items():
            st.markdown(f"**{t}** ({len(vs)}): " + ", ".join(f"`{v}`" for v in vs[:10]))
    else:
        st.info("No se detectaron entidades estructuradas.")

    if aud:
        st.markdown("### 🔍 Auditoría de hechos")
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="doc-card doc-card-ok">', unsafe_allow_html=True)
            st.markdown(f"**✅ Verificados: {len(aud.get('verified', []))}**")
            for v in aud.get("verified", [])[:5]: st.markdown(f"- {v['statement'][:160]}…")
            st.markdown("</div>", unsafe_allow_html=True)
        with cb:
            inc = aud.get("inconsistencies", [])
            cls = "doc-card-warn" if inc else "doc-card-ok"
            st.markdown(f'<div class="doc-card {cls}">', unsafe_allow_html=True)
            st.markdown(f"**⚠️ Inconsistencias: {len(inc)}**")
            for v in inc[:5]: st.markdown(f"- {v['statement'][:160]}…")
            st.markdown("</div>", unsafe_allow_html=True)

    inv = r.get("investigador")
    if inv:
        st.markdown(f"### 🌐 Investigación web: `{inv['entity']}`")
        for res in inv.get("results", []):
            st.markdown(f"- [{res['title']}]({res['url']}) — {res['snippet'][:180]}…")

    st.markdown("### 🧠 Consenso Multi-LLM")
    st.markdown(result["consensus"].get("consensus", "N/A"))

    st.markdown("### 📥 Exportar")
    st.download_button("⬇️ Descargar informe Markdown",
                       data=result["report"].encode("utf-8"),
                       file_name=f"informe_{datetime.now():%Y%m%d_%H%M%S}.md",
                       mime="text/markdown")


if __name__ == "__main__":
    main()
