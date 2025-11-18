import streamlit as st

from utils.auth import login

st.title("🔐 Inicio de Sesión")

username = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if st.button("Ingresar"):
    if login(username, password):
        st.success("Inicio exitoso")
        st.rerun()
    else:
        st.error("Usuario o contraseña incorrectos")

st.page_link("pages/cuentas.py", label="Registrar nuevo usuario")
