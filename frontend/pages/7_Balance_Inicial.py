import streamlit as st
import requests
import pandas as pd
import os
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN (SIEMPRE PRIMERO)
# ==========================================
st.set_page_config(page_title="Balance Inicial", layout="wide", page_icon="🏁")

# ==========================================
# 2. IMPORTS Y AUTH
# ==========================================
try:
    from utils.auth import require_login
    from utils.sidebar import render_sidebar
    require_login()
    render_sidebar()
except ImportError:
    pass

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# ==========================================
# 3. FUNCIONES DE DATOS
# ==========================================

def obtener_cuentas():
    try:
        r = requests.get(f"{API_URL}/cuentas")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
    return []

def obtener_aperturas():
    """Obtiene partidas y filtra solo tipo 'APERTURA'."""
    try:
        r = requests.get(f"{API_URL}/partidas")
        if r.status_code == 200:
            todas = r.json()
            return [p for p in todas if p.get('tipo') == 'APERTURA']
    except:
        pass
    return []

def eliminar_partida(id_partida):
    try:
        r = requests.delete(f"{API_URL}/partidas/{id_partida}")
        return r.status_code in [200, 204]
    except:
        return False

# ==========================================
# 4. SESSION STATE
# ==========================================
if "lineas_apertura" not in st.session_state:
    st.session_state.lineas_apertura = []

if "cuentas_list_apertura" not in st.session_state:
    data = obtener_cuentas()
    # Guardamos lista para selectbox y mapa para buscar datos rápido
    st.session_state.cuentas_list_apertura = [f"{c['codigo']} - {c['nombre']}" for c in data]
    st.session_state.mapa_cuentas_apertura = {f"{c['codigo']} - {c['nombre']}": c for c in data}

# ==========================================
# 5. INTERFAZ
# ==========================================

st.title("🏁 Balance Inicial (Partida de Apertura)")
st.markdown("""
Esta sección registra los saldos iniciales de la empresa.
* **Activos:** Regístralos en el **Debe**.
* **Pasivos y Capital:** Regístralos en el **Haber**.
""")
st.markdown("---")

tab_crear, tab_historial = st.tabs(["➕ Registrar Apertura", "📜 Historial de Aperturas"])

# ---------------------------------------------------------
# TAB 1: CREAR BALANCE INICIAL
# ---------------------------------------------------------
with tab_crear:
    
    # Verificar si ya existe una apertura (Opcional, advertencia visual)
    existentes = obtener_aperturas()
    if existentes:
        st.warning(f"⚠️ Atención: Ya existen {len(existentes)} partidas de apertura registradas en el sistema. Asegúrate de no duplicar saldos iniciales.")

    c1, c2 = st.columns([1, 3])
    with c1:
        fecha = st.date_input("Fecha de Inicio", value=date(date.today().year, 1, 1))
    with c2:
        desc = st.text_input("Descripción", value="Asiento de Apertura / Balance Inicial")

    st.markdown("### 🔢 Ingreso de Cuentas")
    
    with st.container(border=True):
        col_cta, col_debe, col_haber, col_btn = st.columns([3, 1.5, 1.5, 1])
        
        with col_cta:
            cta_sel = st.selectbox("Cuenta", st.session_state.cuentas_list_apertura)
        
        # Callbacks para limpiar el campo opuesto
        def limpiar_haber(): st.session_state.monto_haber_ap = 0.0
        def limpiar_debe(): st.session_state.monto_debe_ap = 0.0

        with col_debe:
            val_debe = st.number_input("Debe (Activos)", min_value=0.0, step=0.01, key="monto_debe_ap", on_change=limpiar_haber)
        
        with col_haber:
            val_haber = st.number_input("Haber (Pasivo/Capital)", min_value=0.0, step=0.01, key="monto_haber_ap", on_change=limpiar_debe)
            
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Agregar", use_container_width=True):
                if val_debe == 0 and val_haber == 0:
                    st.toast("El monto debe ser mayor a 0")
                else:
                    cta_obj = st.session_state.mapa_cuentas_apertura.get(cta_sel, {})
                    st.session_state.lineas_apertura.append({
                        "id_cuenta": cta_obj.get("id_cuenta"),
                        "codigo": cta_obj.get("codigo"),
                        "nombre": cta_obj.get("nombre"),
                        "debe": val_debe,
                        "haber": val_haber
                    })
                    st.rerun()

    # Visualización de la Tabla
    if len(st.session_state.lineas_apertura) > 0:
        df = pd.DataFrame(st.session_state.lineas_apertura)
        st.dataframe(
            df[["codigo", "nombre", "debe", "haber"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "debe": st.column_config.NumberColumn("Debe ($)", format="$ %.2f"),
                "haber": st.column_config.NumberColumn("Haber ($)", format="$ %.2f"),
            }
        )
        
        if st.button("Limpiar Lista"):
            st.session_state.lineas_apertura = []
            st.rerun()

    st.markdown("---")
    
    # Cálculos y Ecuación Contable
    t_debe = sum(l['debe'] for l in st.session_state.lineas_apertura)
    t_haber = sum(l['haber'] for l in st.session_state.lineas_apertura)
    diff = t_debe - t_haber
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Activos (Debe)", f"${t_debe:,.2f}")
    m2.metric("Total Pasivo + Capital (Haber)", f"${t_haber:,.2f}")
    
    cuadrado = abs(diff) < 0.01
    txt_diff = "✅ Ecuación Cuadrada" if cuadrado else f"❌ Diferencia: ${diff:,.2f}"
    m3.metric("Estado", txt_diff, delta=None if cuadrado else diff, delta_color="normal" if cuadrado else "inverse")
    
    # Botón de Guardado
    col_s1, col_s2 = st.columns([4, 1])
    with col_s2:
        puede_guardar = cuadrado and len(st.session_state.lineas_apertura) > 0
        if st.button("💾 Guardar Balance Inicial", type="primary", disabled=not puede_guardar, use_container_width=True):
            
            detalles_payload = [
                {
                    "id_cuenta": l["id_cuenta"], 
                    "debe": l["debe"], 
                    "haber": l["haber"]
                } for l in st.session_state.lineas_apertura
            ]
            
            payload = {
                "fecha": str(fecha),
                "descripcion": desc,
                "tipo": "APERTURA",  # <--- ETIQUETA CLAVE
                "detalles": detalles_payload
            }
            
            try:
                with st.spinner("Registrando apertura..."):
                    r = requests.post(f"{API_URL}/partidas", json=payload)
                    if r.status_code == 200:
                        st.balloons()
                        st.success("Balance Inicial registrado.")
                        st.session_state.lineas_apertura = []
                        st.rerun()
                    else:
                        st.error(f"Error: {r.text}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# TAB 2: HISTORIAL
# ---------------------------------------------------------
with tab_historial:
    st.subheader("Historial de Aperturas")
    
    if st.button("🔄 Actualizar lista"):
        st.rerun()

    aperturas = obtener_aperturas()
    if not aperturas:
        st.info("No hay balances iniciales registrados.")
    else:
        for p in aperturas:
            with st.expander(f"📅 {p['fecha']} - {p['descripcion']} (ID: {p['id_partida']})"):
                
                # Tabla de detalles
                filas = []
                for d in p.get('detalles', []):
                    filas.append({
                        "ID Cta": d['id_cuenta'],
                        "Debe": d['debe'],
                        "Haber": d['haber']
                    })
                st.dataframe(pd.DataFrame(filas), use_container_width=True)
                
                # Botón Eliminar
                if st.button("🗑️ Eliminar esta apertura", key=f"del_{p['id_partida']}"):
                    if eliminar_partida(p['id_partida']):
                        st.success("Eliminada.")
                        st.rerun()
                    else:
                        st.error("Error al eliminar.")