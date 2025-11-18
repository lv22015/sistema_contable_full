import streamlit as st
import requests
import os
from utils.auth import require_login
from utils.sidebar import render_sidebar

# ==============================
# CONFIGURACIÓN DEL BACKEND
# ==============================
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

require_login()
render_sidebar()

st.set_page_config(page_title="Catálogo de Cuentas", layout="wide")
st.title("Catálogo de Cuentas Contables")

# ==============================
# FUNCIONES AUXILIARES
# ==============================

def cargar_cuentas():
    try:
        r = requests.get(f"{BACKEND_URL}/cuentas/")
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Error al cargar cuentas: {r.text}")
            return []
    except Exception as e:
        st.error(f"Error de conexión con backend: {e}")
        return []


def crear_cuenta(payload):
    try:
        r = requests.post(f"{BACKEND_URL}/cuentas/", json=payload)
        if r.status_code == 200:
            st.success("Cuenta creada exitosamente")
            st.session_state["refresh"] = True
        else:
            st.error(f" Error: {r.text}")
    except Exception as e:
        st.error(f"Error de conexión con backend: {e}")


def actualizar_cuenta(id_cuenta, payload):
    try:
        r = requests.put(f"{BACKEND_URL}/cuentas/{id_cuenta}", json=payload)
        if r.status_code == 200:
            st.success("Cuenta actualizada correctamente")
            st.session_state["refresh"] = True
        else:
            st.error(f"Error al actualizar: {r.text}")
    except Exception as e:
        st.error(f"Error de conexión con backend: {e}")


def eliminar_cuenta(id_cuenta):
    try:
        r = requests.delete(f"{BACKEND_URL}/cuentas/{id_cuenta}")
        if r.status_code == 200:
            st.success("Cuenta eliminada correctamente")
            st.session_state["refresh"] = True
        else:
            st.error(f"Error al eliminar: {r.text}")
    except Exception as e:
        st.error(f"Error de conexión con backend: {e}")


# ==============================
# FORMULARIO CRUD
# ==============================

st.sidebar.header("Gestión de cuentas")

modo = st.sidebar.radio("Seleccione una acción:", ["Agregar", "Editar", "Eliminar"])

cuentas = cargar_cuentas()

if modo == "Agregar":
    st.subheader("Agregar nueva cuenta")

    with st.form("crear_cuenta"):
        codigo = st.text_input("Código de cuenta")
        nombre = st.text_input("Nombre de cuenta")
        tipo = st.selectbox("Tipo de cuenta", ["Activo", "Pasivo", "Capital", "Ingreso", "Gasto"])

        submitted = st.form_submit_button("Guardar")
        if submitted:
            if not codigo or not nombre:
                st.warning("Complete todos los campos.")
            else:
                crear_cuenta({"codigo": codigo, "nombre": nombre, "tipo": tipo})


elif modo == "Editar":
    st.subheader("Editar cuenta existente")

    if cuentas:
        opciones = {f"{c['codigo']} - {c['nombre']}": c for c in cuentas}
        seleccion = st.selectbox("Seleccione una cuenta", list(opciones.keys()))
        cuenta = opciones[seleccion]

        with st.form("editar_cuenta"):
            nuevo_nombre = st.text_input("Nombre", cuenta["nombre"])
            nuevo_tipo = st.selectbox("Tipo", ["Activo", "Pasivo", "Capital", "Ingreso", "Gasto"], index=["Activo", "Pasivo", "Capital", "Ingreso", "Gasto"].index(cuenta["tipo"]))

            submitted = st.form_submit_button("Actualizar")
            if submitted:
                actualizar_cuenta(cuenta["id_cuenta"], {
                    "codigo": cuenta["codigo"],
                    "nombre": nuevo_nombre,
                    "tipo": nuevo_tipo,
                    "nivel": cuenta["nivel"],
                    "cuenta_padre": cuenta["cuenta_padre"]
                })
    else:
        st.info("No hay cuentas registradas.")


elif modo == "Eliminar":
    st.subheader("Eliminar cuenta")

    if cuentas:
        opciones = {f"{c['codigo']} - {c['nombre']}": c for c in cuentas}
        seleccion = st.selectbox("Seleccione una cuenta a eliminar", list(opciones.keys()))
        cuenta = opciones[seleccion]

        if st.button("Eliminar permanentemente"):
            eliminar_cuenta(cuenta["id_cuenta"])
    else:
        st.info("No hay cuentas registradas.")


# ==============================
# LISTADO DE CUENTAS
# ==============================

st.divider()
st.subheader("Listado de Cuentas Registradas")

if "refresh" in st.session_state and st.session_state["refresh"]:
    st.session_state["refresh"] = False
    st.rerun()

if cuentas:
    st.dataframe(cuentas, use_container_width=True)
else:
    st.info("No hay cuentas registradas aún.")
