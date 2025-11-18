import streamlit as st
from utils.auth import require_login, register_user


st.title("📝 Registrar Usuario")

username = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")
nombre = st.text_input("Nombre completo")
rol = st.selectbox("Rol", ["admin", "usuario"])

if st.button("Registrar"):
    if register_user(username, password, nombre, rol):
        st.success("Usuario creado correctamente")
    else:
        st.error("No se pudo registrar el usuario")
