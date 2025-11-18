import streamlit as st
from utils.auth import logout

def render_sidebar():
    if not st.session_state.get("logged", False):
        return

    user = st.session_state.get("user", "Usuario")
    rol = st.session_state.get("rol", "usuario")

    with st.sidebar:
        st.title("📌 Panel de Control")
        st.write(f"👤 {user}")
        st.write(f"🔑 Rol: {rol}")
        st.write("---")

        st.page_link("pages/panel.py", label="🏠 Panel Principal")
        st.page_link("pages/1_Catalogo_de_Cuentas.py", label="📘 Catálogo de Cuentas")
        st.page_link("pages/2_Manual_de_Cuentas.py", label="📗 Manual de Cuentas")
        st.page_link("pages/3_Partidas_Diario.py", label="📙 Partidas Diario")
        st.page_link("pages/4_Mayorizacion.py", label="📘 Mayorización")
        st.page_link("pages/5_Partidas_Ajuste.py", label="📗 Partidas Ajuste")
        st.page_link("pages/6_Balanza_Comprobacion.py", label="📘 Balanza de Comprobación")
        st.page_link("pages/7_Balance_Inicial.py", label="📙 Balance Inicial")
        st.page_link("pages/8_Estados_Financieros.py", label="📗 Estados Financieros")
        st.page_link("pages/9_Facturacion_y_Ventas.py", label="📘 Facturación y Ventas")

        if rol == "admin":
            st.page_link("pages/cuentas.py", label="👤 Gestión de Usuarios")

        st.write("---")
        st.button("Cerrar Sesión", on_click=logout)
