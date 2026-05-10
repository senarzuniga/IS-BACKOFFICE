import streamlit as st
from backoffice.ui.market_intelligence_panel import render_market_intelligence_panel

st.set_page_config(page_title="Intelligence Panel", page_icon="🕵️", layout="wide")
st.title("🕵️ Intelligence Panel")
render_market_intelligence_panel()
