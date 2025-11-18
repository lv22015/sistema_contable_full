
import streamlit as st

from utils.auth import require_login
from utils.sidebar import render_sidebar

require_login()
render_sidebar()
st.title("📘 Partidas - Diario")
st.write("Página: Partidas - Diario. Implementa aquí los formularios y llamadas a la API.")
