import streamlit as st
import requests
import pandas as pd
import os
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA (SIEMPRE PRIMERO)
# ==========================================
st.set_page_config(page_title="Partidas de Ajuste", layout="wide", page_icon="⚖️")

# ==========================================
# 2. IMPORTS DE UTILS Y AUTH
# ==========================================
# Intentamos importar utils, si falla (local), pasamos
try:
    from utils.auth import require_login
    from utils.sidebar import render_sidebar
    require_login()
    render_sidebar()
except ImportError:
    pass

# Configuración de la API
API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# ==========================================
# 3. FUNCIONES AUXILIARES
# ==========================================

def obtener_cuentas():
    """Obtiene el catálogo de cuentas para el selector."""
    try:
        r = requests.get(f"{API_URL}/cuentas")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Error conectando al backend: {e}")
    return []

def obtener_ajustes():
    """Obtiene TODAS las partidas y filtra solo las de tipo 'AJUSTE'."""
    try:
        r = requests.get(f"{API_URL}/partidas")
        if r.status_code == 200:
            todas = r.json()
            # Filtramos solo las que son de ajuste
            ajustes = [p for p in todas if p.get('tipo') == 'AJUSTE']
            return ajustes
    except:
        pass
    return []

def eliminar_partida(id_partida):
    """Elimina una partida por ID."""
    try:
        r = requests.delete(f"{API_URL}/partidas/{id_partida}")
        return r.status_code in [200, 204]
    except:
        return False

# ==========================================
# 4. ESTADO DE LA SESIÓN (SESSION STATE)
# ==========================================
if "lineas_ajuste" not in st.session_state:
    st.session_state.lineas_ajuste = []

if "cuentas_list_ajuste" not in st.session_state:
    data_cuentas = obtener_cuentas()
    # Crear lista formateada "CODIGO - NOMBRE"
    st.session_state.cuentas_list_ajuste = [f"{c['codigo']} - {c['nombre']}" for c in data_cuentas]
    # Mapa auxiliar para buscar IDs rápido
    st.session_state.mapa_cuentas_ajuste = {f"{c['codigo']} - {c['nombre']}": c for c in data_cuentas}

# Variables para inputs numéricos (para limpiar después de agregar)
if "ajuste_debe" not in st.session_state:
    st.session_state.ajuste_debe = 0.00
if "ajuste_haber" not in st.session_state:
    st.session_state.ajuste_haber = 0.00

# Callbacks para exclusividad Debe/Haber
def _clear_haber_ajuste():
    st.session_state.ajuste_haber = 0.00

def _clear_debe_ajuste():
    st.session_state.ajuste_debe = 0.00

# ==========================================
# 5. INTERFAZ GRÁFICA
# ==========================================

st.title("⚖️ Partidas de Ajuste")
st.markdown("Registro de depreciaciones, amortizaciones, correcciones y provisiones.")
st.markdown("---")

tab_crear, tab_listar = st.tabs(["➕ Nuevo Ajuste", "📋 Ver Ajustes"])

# ---------------------------------------------------------
# TAB 1: CREAR AJUSTE
# ---------------------------------------------------------
with tab_crear:
    
    # A. CABECERA
    c_head1, c_head2 = st.columns([1, 3])
    with c_head1:
        fecha = st.date_input("Fecha de Ajuste", value=date.today())
    with c_head2:
        descripcion = st.text_input("Descripción / Razón del Ajuste", placeholder="Ej: Depreciación mensual de mobiliario")

    st.markdown("### 📝 Detalle del Asiento")

    # B. FORMULARIO DE LÍNEA
    with st.container():
        col_inp1, col_inp2, col_inp3, col_btn = st.columns([3, 1.5, 1.5, 1])
        
        with col_inp1:
            cuenta_sel = st.selectbox("Cuenta Afectada", st.session_state.cuentas_list_ajuste, key="sel_cuenta_ajuste")
        
        with col_inp2:
            monto_debe = st.number_input("Debe", min_value=0.00, step=0.01, format="%.2f", key="ajuste_debe", on_change=_clear_haber_ajuste)
        
        with col_inp3:
            monto_haber = st.number_input("Haber", min_value=0.00, step=0.01, format="%.2f", key="ajuste_haber", on_change=_clear_debe_ajuste)
            
        with col_btn:
            st.write("") # Espaciador vertical
            st.write("") 
            if st.button("➕ Agregar", key="btn_add_ajuste", use_container_width=True):
                # Validaciones
                if monto_debe == 0 and monto_haber == 0:
                    st.toast("⚠️ Debe ingresar un monto mayor a 0.", icon="⚠️")
                elif monto_debe > 0 and monto_haber > 0:
                    st.toast("⛔ No puede cargar y abonar la misma línea.", icon="⛔")
                else:
                    # Obtener datos de la cuenta desde el mapa
                    cta_obj = st.session_state.mapa_cuentas_ajuste.get(cuenta_sel, {})
                    
                    st.session_state.lineas_ajuste.append({
                        "id_cuenta": cta_obj.get("id_cuenta"),
                        "codigo": cta_obj.get("codigo"),
                        "nombre": cta_obj.get("nombre"),
                        "debe": monto_debe,
                        "haber": monto_haber
                    })
                    st.rerun()

    # C. TABLA DE PREVISUALIZACIÓN
    if len(st.session_state.lineas_ajuste) > 0:
        df_lines = pd.DataFrame(st.session_state.lineas_ajuste)
        
        # Mostrar tabla limpia
        st.dataframe(
            df_lines[["codigo", "nombre", "debe", "haber"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "codigo": "Código",
                "nombre": "Cuenta",
                "debe": st.column_config.NumberColumn("Debe ($)", format="$ %.2f"),
                "haber": st.column_config.NumberColumn("Haber ($)", format="$ %.2f"),
            }
        )
        
        if st.button("🗑️ Limpiar todo", key="btn_clear_ajuste"):
            st.session_state.lineas_ajuste = []
            st.rerun()
    else:
        st.info("Agregue cuentas para formar la partida de ajuste.")

    st.markdown("---")

    # D. TOTALES Y GUARDADO
    total_debe = sum(l['debe'] for l in st.session_state.lineas_ajuste)
    total_haber = sum(l['haber'] for l in st.session_state.lineas_ajuste)
    diff = total_debe - total_haber
    
    # Métricas de cuadre
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Debe", f"${total_debe:,.2f}")
    m2.metric("Total Haber", f"${total_haber:,.2f}")
    
    estado_ok = abs(diff) < 0.01
    txt_estado = "✅ CUADRADO" if estado_ok else f"❌ DIFERENCIA: ${diff:,.2f}"
    color_estado = "normal" if estado_ok else "inverse"
    m3.metric("Estado", txt_estado, delta=None if estado_ok else diff, delta_color=color_estado)

    # Botón Guardar
    st.write("")
    c_save1, c_save2 = st.columns([4, 1])
    with c_save2:
        # Condiciones para habilitar guardado
        puedo_guardar = estado_ok and len(st.session_state.lineas_ajuste) > 0 and descripcion.strip() != ""
        
        if st.button("💾 Guardar Ajuste", type="primary", disabled=not puedo_guardar, use_container_width=True):
            # 1. Preparar Payload
            detalles_api = []
            for l in st.session_state.lineas_ajuste:
                detalles_api.append({
                    "id_cuenta": l["id_cuenta"],
                    "debe": l["debe"],
                    "haber": l["haber"],
                    "descripcion": None # Opcional por línea
                })
            
            payload = {
                "fecha": str(fecha),
                "descripcion": descripcion,
                "tipo": "AJUSTE",  # <--- IMPORTANTE: TIPO ESPECÍFICO
                "detalles": detalles_api
            }

            # 2. Enviar a API
            try:
                with st.spinner("Registrando ajuste contable..."):
                    r = requests.post(f"{API_URL}/partidas", json=payload)
                    
                    if r.status_code == 200:
                        st.balloons()
                        st.success("¡Partida de Ajuste registrada correctamente!")
                        # Limpiar form
                        st.session_state.lineas_ajuste = []
                        st.rerun()
                    else:
                        st.error(f"Error del servidor: {r.status_code} - {r.text}")
            except Exception as e:
                st.error(f"No se pudo conectar: {e}")

    if not puedo_guardar and len(st.session_state.lineas_ajuste) > 0:
        if descripcion.strip() == "":
            st.warning("⚠️ Falta agregar una descripción.")
        elif not estado_ok:
            st.error("⚠️ La partida no cuadra.")

# ---------------------------------------------------------
# TAB 2: LISTAR AJUSTES
# ---------------------------------------------------------
with tab_listar:
    st.subheader("📋 Historial de Ajustes")
    
    if st.button("🔄 Refrescar lista"):
        st.rerun()
        
    ajustes = obtener_ajustes()
    
    if not ajustes:
        st.info("No se encontraron partidas de tipo 'AJUSTE'.")
    else:
        # Ordenar por fecha descendente (más reciente arriba)
        ajustes_sorted = sorted(ajustes, key=lambda x: x['fecha'], reverse=True)
        
        for p in ajustes_sorted:
            label = f"📅 {p['fecha']} | {p['descripcion']} (ID: {p['id_partida']})"
            with st.expander(label):
                c_info1, c_info2 = st.columns([3, 1])
                with c_info1:
                    st.write(f"**Concepto:** {p['descripcion']}")
                with c_info2:
                    if st.button("🗑️ Eliminar", key=f"del_ajuste_{p['id_partida']}"):
                        if eliminar_partida(p['id_partida']):
                            st.success("Eliminado.")
                            st.rerun()
                        else:
                            st.error("Error al eliminar.")
                
                # Tabla de detalles
                filas_det = []
                for d in p.get('detalles', []):
                    filas_det.append({
                        "Cuenta ID": d['id_cuenta'],
                        "Debe": d['debe'],
                        "Haber": d['haber']
                    })
                
                if filas_det:
                    st.dataframe(pd.DataFrame(filas_det), use_container_width=True)