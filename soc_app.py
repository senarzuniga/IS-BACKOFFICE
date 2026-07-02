from __future__ import annotations

import random
from typing import Dict, List
import streamlit as st


# Mock configuration
COMPANIES = ['Ingecart', 'IAR', 'Consulting Mode']
MODES = ['Executive', 'Strategic', 'Technical', 'Consulting']


def _mock_profiles() -> Dict[str, Dict]:
    return {
        'Ingecart': {
            'revenue': '€2.5M',
            'projected_revenue': '€3.2M',
            'pipeline': '€7M',
            'projects': 5,
            'customers': ['International Paper', 'Cascades', 'President Container'],
            'competitors': ['PARA SRL', 'FUNCEN', 'DGM Europe'],
        },
        'IAR': {
            'revenue': '€1.1M',
            'projected_revenue': '€1.4M',
            'pipeline': '€2.3M',
            'projects': 3,
            'customers': ['LocalCo A', 'LocalCo B'],
            'competitors': ['FUNCEN'],
        },
        'Consulting Mode': {
            'revenue': 'N/A',
            'projected_revenue': 'N/A',
            'pipeline': 'N/A',
            'projects': 0,
            'customers': [],
            'competitors': ['PARA SRL', 'FUNCEN', 'DGM Europe'],
        },
    }


def generate_mock_ai_response(company: str, mode: str, question: str) -> Dict:
    # Simple rule-based mock responder
    prof = _mock_profiles().get(company, {})
    q = (question or '').strip()
    if not q:
        return {
            'summary': 'Please enter a strategic question to receive an executive-style answer.',
            'risks': [],
            'opportunities': [],
            'recommendations': [],
            'confidence': 0.0,
        }

    # keywords
    risks = []
    opps = []
    recs = []

    if 'scale' in q.lower() or 'revenue' in q.lower():
        recs.append('Focus on repeatable service products and standardize delivery to enable scaling.')
        opps.append('Leverage existing large accounts for pilot subscription services.')
        risks.append('Over-reliance on project-based revenue limits scalability.')

    if 'usa' in q.lower() or 'expansion' in q.lower():
        recs.append('Validate regulatory and distribution requirements before committing resources.')
        opps.append('Target niche service offerings with high margins in USA initial launch.')
        risks.append('High operational cost and local competition risk.')

    if 'mtorres' in q.lower() or 'partnership' in q.lower():
        recs.append('Keep negotiation options flexible; avoid exclusivity clauses early.')
        opps.append('A partnership can accelerate go-to-market for large accounts.')
        risks.append('Potential lock-in or channel conflict with existing customers.')

    # default fallbacks
    if not recs:
        recs.append('Prioritize three action items: stabilize operations, pilot a repeatable service, and capture KPIs.')
    if not opps:
        opps.append('Optimize pricing signals and target high-value niches.')
    if not risks:
        risks.append('Operational capacity and service delivery variability.')

    # summary
    summary_lines: List[str] = []
    summary_lines.append(f"Executive view for {company} ({mode} mode):")
    if prof:
        summary_lines.append(f"Revenue: {prof.get('revenue')} · Pipeline: {prof.get('pipeline')}")
    summary_lines.append(f"Question: {q}")
    summary_lines.append('Top recommendation: ' + recs[0])

    return {
        'summary': ' '.join(summary_lines),
        'risks': risks,
        'opportunities': opps,
        'recommendations': recs,
        'confidence': round(random.uniform(0.6, 0.92), 2),
    }


def main():
    st.set_page_config(page_title='SOC Intelligence Dashboard', layout='wide')
    st.title('SOC — Intelligence Dashboard (v1, mock)')

    # Top selectors
    left, right = st.columns([2, 1])
    with left:
        company = st.selectbox('Company', COMPANIES, index=0)
        mode = st.selectbox('Mode', MODES, index=0)
    with right:
        st.write('')
        st.markdown('**System Status**')
        st.write('UI Ready: ✅')
        st.write('Indexing: ⛔ NOT RUNNING')
        st.write('Data Layer: MOCK / EMPTY')
        st.write('AI Engine: MOCK ACTIVE')

    st.markdown('---')

    # Main layout: left panels for AI + KPIs, right for knowledge explorer
    col_ai, col_side = st.columns([2, 1])

    with col_ai:
        st.header('Ask Strategic Question')
        question = st.text_area('Enter your strategic question here', height=120)
        if st.button('Ask AI'):
            resp = generate_mock_ai_response(company, mode, question)
            st.subheader('Executive Analysis')
            st.write(resp['summary'])
            st.markdown('**Risks**')
            for r in resp['risks']:
                st.write('- ' + r)
            st.markdown('**Opportunities**')
            for o in resp['opportunities']:
                st.write('- ' + o)
            st.markdown('**Recommendations**')
            for rc in resp['recommendations']:
                st.write('- ' + rc)
            st.caption(f"Confidence: {resp['confidence']}")
        else:
            st.info('Ask a question to get an executive-style mock answer. UI works without data.')

        st.markdown('---')
        st.header('KPI Dashboard')
        prof = _mock_profiles().get(company, {})
        k1, k2, k3, k4 = st.columns(4)
        k1.metric('Revenue', prof.get('revenue', 'N/A'))
        k2.metric('Projected Revenue', prof.get('projected_revenue', 'N/A'))
        k3.metric('Pipeline', prof.get('pipeline', 'N/A'))
        k4.metric('Active Projects', prof.get('projects', 0))

        st.markdown('---')
        st.header('Competitive Intelligence (Beta)')
        for comp in prof.get('competitors', ['PARA SRL', 'FUNCEN', 'DGM Europe']):
            st.write(f"- {comp} — Status: No data / placeholder")

    with col_side:
        st.header('Local Knowledge Explorer (mock)')
        qlocal = st.text_input('Search local knowledge (mock)')
        docs = ['MTorres_agreement_v3.md', 'USA_strategy_notes.txt', 'service_model_analysis.md']
        if qlocal:
            matched = [d for d in docs if qlocal.lower() in d.lower()]
            if matched:
                for m in matched:
                    st.write(f'- {m} (placeholder)')
            else:
                st.info('No local documents match (mock search)')
        else:
            st.write('Recent documents:')
            for d in docs:
                st.write('- ' + d)

        st.markdown('---')
        st.header('System Status')
        st.write('Indexing: NOT RUNNING')
        st.write('Background Workers: OFF')
        st.write('Knowledge Graph: INITIALIZING (mock)')

    st.markdown('---')
    st.caption('SOC v1 — Mock interface. No indexing, no file access, no scraping.')


if __name__ == '__main__':
    main()
