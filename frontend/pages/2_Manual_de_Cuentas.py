import streamlit as st
import pandas as pd
import requests
import os
from utils.auth import require_login
from utils.sidebar import render_sidebar

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

require_login()
render_sidebar()

st.set_page_config(page_title="Manual de Cuentas", layout="wide")
st.title("Manual de Cuentas Contables")

# ===========================
# Funciones auxiliares
# ===========================

def obtener_cuentas():
    try:
        r = requests.get(f"{BACKEND_URL}/cuentas/")
        if r.status_code == 200:
            return r.json()
        else:
            st.error("No se pudieron cargar las cuentas.")
            return []
    except Exception as e:
        st.error(f"Error de conexión con backend: {e}")
        return []

def obtener_manual():
    try:
        r = requests.get(f"{BACKEND_URL}/manual_cuentas/")
        if r.status_code == 200:
            return r.json()
        else:
            st.error("No se pudieron cargar los registros del manual.")
            return []
    except Exception as e:
        st.error(f"Error de conexión con backend: {e}")
        return []

def crear_manual(data):
    r = requests.post(f"{BACKEND_URL}/manual_cuentas/", json=data)
    if r.status_code == 200:
        st.success("Descripción agregada correctamente")
    else:
        st.error(f"Error al crear: {r.text}")

def actualizar_manual(id_manual, data):
    r = requests.put(f"{BACKEND_URL}/manual_cuentas/{id_manual}", json=data)
    if r.status_code == 200:
        st.success("Descripción actualizada")
    else:
        st.error(f"Error al actualizar: {r.text}")

def eliminar_manual(id_manual):
    r = requests.delete(f"{BACKEND_URL}/manual_cuentas/{id_manual}")
    if r.status_code == 200:
        st.success("Eliminado correctamente")
    else:
        st.error(f"Error al eliminar: {r.text}")

# ===========================
# CRUD en interfaz
# ===========================

modo = st.sidebar.radio("Acción:", ["Agregar", "Editar", "Eliminar"])
cuentas = obtener_cuentas()
manual = obtener_manual()

if modo == "Agregar":
    st.subheader("Agregar descripción al manual")
    opciones = {f"{c['codigo']} - {c['nombre']}": c['id_cuenta'] for c in cuentas}
    with st.form("crear_manual"):
        cuenta = st.selectbox("Cuenta", list(opciones.keys()))
        descripcion = st.text_area("Descripción de la cuenta")
        ejemplos = st.text_area("Ejemplos de uso")
        enviado = st.form_submit_button("Guardar")
        if enviado:
            crear_manual({
                "id_cuenta": opciones[cuenta],
                "descripcion": descripcion,
                "ejemplos": ejemplos
            })

elif modo == "Editar":
    st.subheader("Editar registro del manual")
    if manual:
        opciones = {f"{m['id_manual']} - Cuenta {m['id_cuenta']}": m for m in manual}
        seleccion = st.selectbox("Seleccione un registro", list(opciones.keys()))
        registro = opciones[seleccion]
        with st.form("editar_manual"):
            nueva_desc = st.text_area("Descripción", registro["descripcion"])
            nuevos_ejemplos = st.text_area("Ejemplos", registro["ejemplos"] or "")
            enviado = st.form_submit_button("Actualizar")
            if enviado:
                actualizar_manual(registro["id_manual"], {
                    "id_cuenta": registro["id_cuenta"],
                    "descripcion": nueva_desc,
                    "ejemplos": nuevos_ejemplos
                })
    else:
        st.info("No hay registros en el manual aún.")

elif modo == "Eliminar":
    st.subheader("Eliminar descripción del manual")
    if manual:
        opciones = {f"{m['id_manual']} - Cuenta {m['id_cuenta']}": m for m in manual}
        seleccion = st.selectbox("Seleccione un registro", list(opciones.keys()))
        registro = opciones[seleccion]
        if st.button("Eliminar"):
            eliminar_manual(registro["id_manual"])
    else:
        st.info("No hay registros para eliminar.")

# ===========================
# Mostrar manual completo
# ===========================

st.divider()
st.subheader("Manual de Cuentas Registrado")

manual = obtener_manual()
if manual:
    df = pd.DataFrame(manual)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aún no hay registros en el manual.")
