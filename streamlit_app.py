import streamlit as st

st.set_page_config(
    page_title="IS-BACKOFFICE – AI Back Office Intelligence",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

from backoffice.ui.app import main  # noqa: E402

main()
