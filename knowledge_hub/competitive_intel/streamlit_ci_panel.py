"""Streamlit panel skeleton for Competitive Intelligence.

Run with: `streamlit run knowledge_hub/competitive_intel/streamlit_ci_panel.py`
"""

from __future__ import annotations

import streamlit as st
from knowledge_hub.competitive_intel.source_registry import SourceRegistry
from knowledge_hub.competitive_intel.hybrid_retrieval import HybridRetrieval
from knowledge_hub.competitive_intel.evidence_store import EvidenceStore
from knowledge_hub.competitive_intel.citation_builder import CitationBuilder
from knowledge_hub.competitive_intel.quality_gate import QualityGate
from knowledge_hub.competitive_intel.competitor_report_generator import CompetitorReportGenerator


def main():
    st.set_page_config(page_title='Competitive Intelligence', layout='wide')

    st.sidebar.title('Competitive Intelligence')
    registry = SourceRegistry()
    companies = sorted({s['company'] for s in registry.list_sources()})
    company = st.sidebar.selectbox('Company scope', options=['Ingecart'] + companies)
    action = st.sidebar.radio('Action', options=['Search', 'Sources', 'Generate Report'])

    evidence = EvidenceStore()
    citations = CitationBuilder(evidence)
    retriever = HybridRetrieval()
    gate = QualityGate()
    generator = CompetitorReportGenerator(retriever, citations, evidence, gate)

    if action == 'Sources':
        st.header('Registered Sources')
        for s in registry.list_sources(company=None):
            st.write(s)

    elif action == 'Search':
        q = st.text_input('Query')
        if q:
            results = retriever.keyword_search(company, q, limit=12)
            for r in results:
                st.subheader(r.get('file'))
                st.write(r.get('summary'))

    else:
        st.header('Generate competitor report')
        competitor = st.text_input('Competitor name')
        query = st.text_input('Search query', value='company overview')
        if st.button('Generate'):
            report = generator.generate(company, competitor or 'Unknown', query)
            st.subheader('Findings')
            for f in report['findings']:
                st.write(f)
            st.subheader('Evidence')
            for c in report['evidence']:
                st.write(c)
            st.info(f"Quality: {report['quality']}")


if __name__ == '__main__':
    main()
