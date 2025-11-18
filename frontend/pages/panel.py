import streamlit as st
from utils.auth import require_login
from utils.sidebar import render_sidebar

require_login()
render_sidebar()

st.title("📊 Panel Principal")
st.write("Bienvenido al sistema contable")
