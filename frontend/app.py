import streamlit as st
from utils.auth import require_login
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Sistema Contable", layout="wide")

# Mostrar sidebar en la aplicación principal
render_sidebar()

# Si no hay login, mostrar enlace al login y detener ejecución
if not st.session_state.get("logged", False):
    st.info("No ha iniciado sesión.")
    # Enlace a la página de login (archivo en pages/login.py)
    st.page_link("pages/login.py", label="🔐 Ir a Inicio de Sesión")
    st.stop()

st.title("Sistema Contable")
st.write("Seleccione una página desde el menú lateral.")
