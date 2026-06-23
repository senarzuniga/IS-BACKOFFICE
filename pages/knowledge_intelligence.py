"""Streamlit page for the Knowledge Intelligence multi-agent system."""

import streamlit as st
from pathlib import Path

from agents.knowledge_intelligence.utils.llm_client import LLMClient
from agents.knowledge_intelligence.memory.knowledge_memory import KnowledgeMemory
from agents.knowledge_intelligence.orchestrator import KnowledgeOrchestrator


def main():
    st.title("🧠 Inteligencia de Conocimiento")
    st.markdown("Lanza un proceso multiagente para investigar, estructurar y redactar un informe de inteligencia.")

    request = st.text_area("Solicitud de investigación (describe lo que quieres investigar)", height=150)
    default_paths = "data;backoffice;docs"
    search_paths_input = st.text_input("Rutas a buscar en repositorio local (separadas por `;`)", value=default_paths)
    search_paths = [p.strip() for p in search_paths_input.split(';') if p.strip()]
    max_iterations = st.slider("Máximo de iteraciones de investigación", min_value=1, max_value=5, value=3)

    if st.button("Iniciar Análisis"):
        if not request.strip():
            st.error("Escribe una solicitud válida para iniciar la investigación.")
            return

        status = st.empty()
        pbar = st.progress(0)
        log_box = st.empty()

        def progress_callback(message: str, progress: float):
            try:
                status.markdown(f"**{message}**")
                pbar.progress(int(max(0, min(100, progress))))
                log_box.text(message)
            except Exception:
                pass

        llm = LLMClient()
        memory = KnowledgeMemory(base_path='data/knowledge_memory')
        orchestrator = KnowledgeOrchestrator(llm, memory, search_paths, progress_callback=progress_callback)

        with st.spinner('Ejecutando orquestador — esto puede tardar varios minutos dependiendo de la configuración...'):
            result = orchestrator.run(request)

        st.success("Proceso completado")

        if result.get('executive_summary'):
            summary = result['executive_summary'].get('summary') if isinstance(result['executive_summary'], dict) else result['executive_summary']
            st.header("Resumen Ejecutivo")
            st.markdown(summary)

        report_file = result.get('report_file') or result.get('file') or result.get('report')
        if report_file and Path(report_file).exists():
            st.header("Informe generado")
            st.markdown(f"**Archivo:** {report_file}")
            with open(report_file, 'r', encoding='utf-8') as f:
                md = f.read()
            st.download_button("Descargar informe (Markdown)", data=md, file_name=Path(report_file).name)
            st.markdown("---")
            st.markdown(md)

        st.info("Requisitos: variable de entorno `OPENAI_API_KEY` set, y dependencias instaladas (openai, playwright, chromadb, etc.).")


if __name__ == '__main__':
    main()
