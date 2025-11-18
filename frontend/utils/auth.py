import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def login(username, password):
    try:
        r = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": username, "password": password}
        )

        if r.status_code == 200:
            data = r.json()

            st.session_state.token = data["access_token"]
            st.session_state.logged = True
            st.session_state.user = data["usuario"]["nombre_completo"]
            st.session_state.rol = data["usuario"]["rol"]

            return True
        return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False


def register_user(username, password, nombre, rol):
    try:
        r = requests.post(
            f"{BACKEND_URL}/auth/register",
            json={
                "username": username,
                "password": password,
                "nombre_completo": nombre,
                "rol": rol
            }
        )
        return r.status_code == 200
    except Exception as e:
        st.error(f"Error: {e}")
        return False


def logout():
    st.session_state.clear()
    st.rerun()


def require_login():
    if not st.session_state.get("logged", False):
        st.switch_page("pages/login.py")
