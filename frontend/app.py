import os

import streamlit as st
st.set_page_config(page_title='Sistema Contable', layout='wide')
st.title('📊 Sistema Contable - Panel Principal')
st.sidebar.title('Navegación')
pages = {
    'Catálogo de Cuentas': 'pages/1_Catalogo_de_Cuentas.py',
    'Manual de Cuentas': 'pages/2_Manual_de_Cuentas.py',
    'Partidas - Diario': 'pages/3_Partidas_Diario.py',
    'Mayorización': 'pages/4_Mayorizacion.py',
    'Partidas de Ajuste': 'pages/5_Partidas_Ajuste.py',
    'Balanza de Comprobación': 'pages/6_Balanza_Comprobacion.py',
    'Balance Inicial': 'pages/7_Balance_Inicial.py',
    'Estados Financieros': 'pages/8_Estados_Financieros.py',
    'Facturación y Ventas': 'pages/9_Facturacion_y_Ventas.py',
    'Usuarios y Auditoría': 'pages/10_Usuarios_y_Auditoria.py',
}

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
st.sidebar.title("Sistema Contable")
st.sidebar.write(f"Conectado al backend: {BACKEND_URL}")


selection = st.sidebar.selectbox("Ir a", list(pages.keys()))
st.sidebar.markdown("**URL Backend (para desarrollo)**")

st.markdown(f"Has seleccionado: **{selection}**")
st.info("Abre el archivo correspondiente en /frontend/pages para implementar la UI de cada módulo.")
