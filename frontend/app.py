import streamlit as st
from utils.auth import require_login
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Sistema Contable", layout="wide")

# Si no hay login, mandar al login directamente
if not st.session_state.get("logged", False):
    st.switch_page("pages/login.py")

# Mostrar sidebar
#render_sidebar()

# Redirección al panel
st.switch_page("pages/panel.py")
