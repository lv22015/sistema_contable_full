
import streamlit as st

from utils.auth import require_login
from utils.sidebar import render_sidebar

require_login()
render_sidebar()
st.title("📘 Estados Financieros")
st.write("Página: Estados Financieros. Implementa aquí los formularios y llamadas a la API.")
