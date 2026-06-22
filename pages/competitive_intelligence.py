import streamlit as st
import os
import time
from agents.competitive_intelligence.orchestrator import run_job


st.set_page_config(page_title="Panel Inteligencia Competitiva", layout="wide")

st.title("Panel de Inteligencia Competitiva — IS-BACKOFFICE")

with st.form("job_form"):
    company = st.text_input("Nombre del competidor (ej: PARA SRL)")
    seeds = st.text_area("Seed URLs (una por línea, opcional)")
    mode = st.selectbox("Modo", ["demo (no-web)", "full web"])
    submitted = st.form_submit_button("Ejecutar análisis")

if submitted:
    if not company:
        st.error("Indica el nombre del competidor")
    else:
        seeds_list = [s.strip() for s in seeds.splitlines() if s.strip()]
        no_web = mode.startswith("demo")
        st.info("Lanzando job — esto puede tardar en modo full web")
        result = run_job(company, seeds=seeds_list, no_web=no_web)
        st.success(f"Job finalizado: {result['job']['id']}")
        st.markdown("---")
        st.header("Informe generado")
        md = open(result['report'], 'r', encoding='utf-8').read()
        st.markdown(md)
        st.markdown("---")
        st.download_button("Descargar informe (.md)", md, file_name=os.path.basename(result['report']))
