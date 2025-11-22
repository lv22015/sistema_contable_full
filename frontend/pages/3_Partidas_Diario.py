import streamlit as st
import requests
import pandas as pd
import os
from datetime import date

# Configuración de la API
API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="Libro Diario", layout="wide", page_icon="📒")

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def obtener_cuentas():
    """
    Obtiene las cuentas del backend.
    Retorna lista de dicts con campos: {'id_cuenta': int, 'codigo': str, 'nombre': str, ...}
    """
    try:
        r = requests.get(f"{API_URL}/cuentas")
        if r.status_code == 200:
            return r.json()
    except:
        pass
    
    # Retorno dummy por si no hay conexión aún
    return [
        {"id_cuenta": 1, "codigo": "1101", "nombre": "Caja General"},
        {"id_cuenta": 2, "codigo": "1102", "nombre": "Bancos"},
        {"id_cuenta": 3, "codigo": "2101", "nombre": "Cuentas por Pagar"},
        {"id_cuenta": 4, "codigo": "4101", "nombre": "Ventas"},
        {"id_cuenta": 5, "codigo": "5101", "nombre": "Gastos de Sueldos"},
        {"id_cuenta": 6, "codigo": "1201", "nombre": "Mobiliario y Equipo"}
    ]

def obtener_partidas():
    """Obtiene todas las partidas del backend."""
    try:
        r = requests.get(f"{API_URL}/partidas")
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def eliminar_partida(id_partida):
    """Intenta eliminar una partida (requiere endpoint DELETE en backend)."""
    try:
        r = requests.delete(f"{API_URL}/partidas/{id_partida}")
        return r.status_code in [200, 204]
    except:
        return False

# ==========================================
# ESTADO DE LA SESIÓN
# ==========================================
if "lineas" not in st.session_state:
    st.session_state.lineas = []

if "cuentas_list" not in st.session_state:
    data_cuentas = obtener_cuentas()
    st.session_state.cuentas_list = [f"{c['codigo']} - {c['nombre']}" for c in data_cuentas]

if "monto_debe" not in st.session_state:
    st.session_state.monto_debe = 0.00
if "monto_haber" not in st.session_state:
    st.session_state.monto_haber = 0.00

if "editando_id" not in st.session_state:
    st.session_state.editando_id = None

# Callbacks para hacer los campos mutuamente excluyentes
def _clear_haber():
    st.session_state.monto_haber = 0.00

def _clear_debe():
    st.session_state.monto_debe = 0.00

# ==========================================
# INTERFAZ GRÁFICA
# ==========================================

st.title("📒 Registro de Partidas (Libro Diario)")
st.markdown("---")

# Tabs para organizar CREATE / READ
tab_crear, tab_listar = st.tabs(["➕ Crear Partida", "📋 Ver Partidas"])

# ==========================================
# TAB 1: CREAR/EDITAR PARTIDA
# ==========================================
with tab_crear:
    
    # 1. CABECERA DE LA PARTIDA
    col1, col2 = st.columns([1, 3])
    with col1:
        fecha = st.date_input("Fecha de la Partida", value=date.today())
    with col2:
        descripcion = st.text_input("Descripción del Asiento", placeholder="Ej: Venta de mercadería al contado")

    st.markdown("### 📝 Detalle de Movimientos")

    # 2. FORMULARIO PARA AGREGAR LÍNEA
    with st.container():
        c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
        
        with c1:
            cuenta_seleccionada = st.selectbox("Seleccionar Cuenta", st.session_state.cuentas_list)
        
        with c2:
            monto_debe = st.number_input(
                "Debe",
                min_value=0.00,
                step=0.01,
                format="%.2f",
                key="monto_debe",
                on_change=_clear_haber
            )

        with c3:
            monto_haber = st.number_input(
                "Haber",
                min_value=0.00,
                step=0.01,
                format="%.2f",
                key="monto_haber",
                on_change=_clear_debe
            )
            
        with c4:
            st.write("")
            st.write("")
            if st.button("➕ Agregar", use_container_width=True):
                codigo_cuenta = cuenta_seleccionada.split(" - ")[0]
                
                data_cuentas = obtener_cuentas()
                id_cuenta = None
                nombre_cuenta = ""
                for c in data_cuentas:
                    if c.get('codigo') == codigo_cuenta:
                        id_cuenta = c.get('id_cuenta')
                        nombre_cuenta = c.get('nombre', '')
                        break
                
                if monto_debe == 0 and monto_haber == 0:
                    st.toast("⚠️ El monto debe ser mayor a 0 en Debe o Haber", icon="⚠️")
                elif monto_debe > 0 and monto_haber > 0:
                    st.toast("⛔ No se puede registrar en Debe y Haber al mismo tiempo", icon="⛔")
                else:
                    st.session_state.lineas.append({
                        "id_cuenta": id_cuenta,
                        "cuenta": codigo_cuenta,
                        "nombre_cuenta": nombre_cuenta,
                        "debe": monto_debe,
                        "haber": monto_haber
                    })
                    st.rerun()

    # 3. TABLA DE LÍNEAS AGREGADAS
    if len(st.session_state.lineas) > 0:
        df = pd.DataFrame(st.session_state.lineas)
        
        st.dataframe(
            df[["cuenta", "nombre_cuenta", "debe", "haber"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "debe": st.column_config.NumberColumn("Debe ($)", format="$ %.2f"),
                "haber": st.column_config.NumberColumn("Haber ($)", format="$ %.2f"),
            }
        )

        if st.button("🗑️ Limpiar líneas"):
            st.session_state.lineas = []
            st.rerun()

    else:
        st.info("No hay líneas agregadas a esta partida.")

    st.markdown("---")

    # 4. SECCIÓN DE CUADRE
    total_debe = sum(linea['debe'] for linea in st.session_state.lineas)
    total_haber = sum(linea['haber'] for linea in st.session_state.lineas)
    diferencia = total_debe - total_haber

    col_tot1, col_tot2, col_tot3 = st.columns(3)
    col_tot1.metric("Total Debe", f"${total_debe:,.2f}")
    col_tot2.metric("Total Haber", f"${total_haber:,.2f}")

    if abs(diferencia) < 0.01:
        color_delta = "normal"
        texto_estado = "✅ PARTIDA CUADRADA"
        estado_ok = True
    else:
        color_delta = "inverse"
        texto_estado = f"❌ DESCUADRE: ${diferencia:,.2f}"
        estado_ok = False

    col_tot3.metric("Estado", texto_estado, delta=None if estado_ok else diferencia, delta_color=color_delta)

    # 5. BOTÓN DE GUARDADO
    st.write("")
    submit_col1, submit_col2 = st.columns([4, 1])

    with submit_col2:
        puedo_guardar = estado_ok and len(st.session_state.lineas) > 0 and descripcion.strip() != ""
        
        if st.button("💾 Guardar Partida", type="primary", disabled=not puedo_guardar, use_container_width=True):
            detalles = []
            for linea in st.session_state.lineas:
                detalles.append({
                    "id_cuenta": linea["id_cuenta"],
                    "debe": float(linea["debe"]),
                    "haber": float(linea["haber"]),
                    "descripcion": None
                })
            
            payload = {
                "fecha": str(fecha),
                "descripcion": descripcion,
                "tipo": "DIARIO",
                "detalles": detalles
            }
            
            try:
                with st.spinner("Guardando en base de datos..."):
                    r = requests.post(f"{API_URL}/partidas", json=payload)
                    
                    if r.status_code == 200:
                        st.balloons()
                        st.success("¡Partida registrada exitosamente!")
                        st.session_state.lineas = []
                        st.rerun()
                    else:
                        st.error(f"Error en el servidor: {r.status_code} - {r.text}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

    if not puedo_guardar and len(st.session_state.lineas) > 0:
        if descripcion.strip() == "":
            st.warning("⚠️ Falta la descripción.")
        elif not estado_ok:
            st.error("⚠️ La partida no cuadra. Revisa los montos.")

# ==========================================
# TAB 2: LISTAR Y GESTIONAR PARTIDAS (READ, UPDATE, DELETE)
# ==========================================
with tab_listar:
    st.subheader("📋 Partidas Registradas")
    
    partidas = obtener_partidas()
    
    if not partidas:
        st.info("No hay partidas registradas aún.")
    else:
        # Mostrar partidas en tabla expandible
        for idx, partida in enumerate(partidas):
            with st.expander(f"📌 {partida['fecha']} - {partida['descripcion'][:40]}... (ID: {partida['id_partida']})"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write(f"**Fecha:** {partida['fecha']}")
                with col2:
                    st.write(f"**Tipo:** {partida['tipo']}")
                with col3:
                    st.write(f"**ID:** {partida['id_partida']}")
                with col4:
                    pass
                
                st.write(f"**Descripción:** {partida['descripcion']}")
                
                # Mostrar detalles en tabla
                detalles_data = []
                for det in partida['detalles']:
                    detalles_data.append({
                        'Cuenta ID': det['id_cuenta'],
                        'Debe': f"${det['debe']:.2f}",
                        'Haber': f"${det['haber']:.2f}"
                    })
                
                if detalles_data:
                    st.dataframe(pd.DataFrame(detalles_data), use_container_width=True, hide_index=True)
                
                # Botones de acción
                col_acc1, col_acc2, col_acc3 = st.columns(3)
                
                with col_acc1:
                    if st.button(f"✏️ Editar", key=f"edit_{idx}", use_container_width=True):
                        st.info("Función de edición: Elimina esta partida y crea una nueva con los cambios.")
                
                with col_acc2:
                    if st.button(f"🗑️ Eliminar", key=f"del_{idx}", use_container_width=True):
                        if eliminar_partida(partida['id_partida']):
                            st.success(f"✅ Partida {partida['id_partida']} eliminada.")
                            st.rerun()
                        else:
                            st.error(f"❌ No se pudo eliminar la partida. El servidor puede no tener endpoint DELETE.")
                
                with col_acc3:
                    st.write("")  # Espaciador