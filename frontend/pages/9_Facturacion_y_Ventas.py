import streamlit as st
import requests
import pandas as pd
import os
import json
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Facturación y Ventas", layout="wide", page_icon="🧾")

# --- PROTECCIÓN CONTRA ERROR DE FPDF ---
# Intentamos importar. Si falla, creamos una clase "falsa" para que el código no se rompa.
try:
    from fpdf import FPDF
    TIENE_FPDF = True
except ImportError:
    TIENE_FPDF = False
    # Definimos FPDF como una clase vacía para evitar el NameError en la línea "class PDF(FPDF)"
    class FPDF: pass 

try:
    from utils.auth import require_login
    from utils.sidebar import render_sidebar
    require_login()
    render_sidebar()
except ImportError:
    pass

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# ==========================================
# 2. DATOS SIMULADOS
# ==========================================
CLIENTES_DB = [
    "Consumidor Final",
    "Empresa A S.A. de C.V.",
    "Cristian Leon (Cliente Recurrente)",
    "Ander Alvarado",
]

PRODUCTOS_DB = [
    {"id": 1, "nombre": "Venta de producto", "precio": 50.00},
    {"id": 2, "nombre": "Arrendamiento", "precio": 1200.00},
    {"id": 3, "nombre": "Mantenimiento del local", "precio": 150.00},
    {"id": 4, "nombre": "Otros", "precio": 850.00},
]

# ==========================================
# 3. FUNCIONES Y CLASES
# ==========================================
def obtener_cuentas_contables():
    try:
        r = requests.get(f"{API_URL}/cuentas")
        if r.status_code == 200: return r.json()
    except: pass
    return []

def obtener_historial_ventas():
    try:
        r = requests.get(f"{API_URL}/partidas")
        if r.status_code == 200:
            todas = r.json()
            return [p for p in todas if p.get('tipo') == 'VENTA']
    except: pass
    return []

# --- CLASE PDF SEGURA ---
# Solo definimos la lógica real si existe la librería.
# Si no existe, hereda de la clase falsa FPDF que creamos arriba.
class PDF(FPDF):
    def header(self):
        if TIENE_FPDF:
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'FACTURA COMERCIAL', 0, 1, 'C')
            self.ln(5)

    def footer(self):
        if TIENE_FPDF:
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_factura(datos_venta):
    """Genera PDF de forma segura."""
    if not TIENE_FPDF:
        return None

    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Cabecera
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"ID Factura: {datos_venta['id_partida']}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Fecha: {datos_venta['fecha']}", ln=True)
        
        desc = datos_venta.get('descripcion', '')
        cliente = desc.split('-')[0] if '-' in desc else desc
        pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
        pdf.ln(10)

        # Tabla
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(100, 10, "Concepto Contable", 1, 0, 'C', 1)
        pdf.cell(40, 10, "Monto", 1, 1, 'C', 1)

        total = 0
        pdf.set_font("Arial", size=10)
        for d in datos_venta.get('detalles', []):
            # Solo mostramos los cargos (Debe) o abonos (Haber) relevantes
            monto = d['debe'] if d['debe'] > 0 else d['haber']
            # Para no duplicar en visualización, tomamos el 'debe' como total factura
            if d['debe'] > 0:
                total += monto
            
            txt_monto = f"${monto:.2f}"
            pdf.cell(100, 10, f"Cuenta {d['id_cuenta']} ({'Cargo' if d['debe']>0 else 'Abono'})", 1)
            pdf.cell(40, 10, txt_monto, 1, 1, 'R')

        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"TOTAL FACTURA: ${total:.2f}", ln=True, align='R')
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        print(f"Error PDF: {e}")
        return None

# ==========================================
# 4. INTERFAZ
# ==========================================
if "carrito_items" not in st.session_state: st.session_state.carrito_items = []
if "cuentas_ui" not in st.session_state:
    raw = obtener_cuentas_contables()
    st.session_state.cuentas_ui = [f"{c['codigo']} - {c['nombre']}" for c in raw]
    st.session_state.mapa_cuentas = {f"{c['codigo']} - {c['nombre']}": c for c in raw}

st.title("🧾 Facturación y Punto de Venta")

# Aviso visual si falta la librería, pero SIN ROMPER la app
if not TIENE_FPDF:
    st.warning("⚠️ El módulo de PDF no está activo. (Librería 'fpdf' no encontrada en este entorno). Puedes usar JSON.")

st.markdown("---")
tab_factura, tab_historial = st.tabs(["🛒 Nueva Venta", "📂 Historial"])

# --- TAB 1: VENTA ---
with tab_factura:
    c1, c2, c3 = st.columns(3)
    with c1: cliente = st.selectbox("Cliente", CLIENTES_DB)
    with c2: fecha = st.date_input("Fecha", value=date.today())
    with c3: pago = st.selectbox("Pago", ["Contado", "Crédito", "Transferencia"])

    with st.container(border=True):
        cp, cc, cpr, cb = st.columns([3, 1, 1, 1])
        with cp: 
            p_nombres = [p['nombre'] for p in PRODUCTOS_DB]
            prod = st.selectbox("Producto", p_nombres)
            p_base = next((p['precio'] for p in PRODUCTOS_DB if p['nombre'] == prod), 0)
        with cc: cant = st.number_input("Cant.", 1, value=1)
        with cpr: precio = st.number_input("Precio", value=p_base)
        with cb:
            st.write(""); st.write("")
            if st.button("Agregar", use_container_width=True):
                st.session_state.carrito_items.append({
                    "producto": prod, "cantidad": cant, "precio": precio, 
                    "subtotal": cant*precio
                })
                st.rerun()

    if st.session_state.carrito_items:
        df = pd.DataFrame(st.session_state.carrito_items)
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button("Vaciar"): 
            st.session_state.carrito_items = []; st.rerun()
        
        subtotal = df['subtotal'].sum()
        col_conf, col_tot = st.columns([2, 1])
        with col_conf:
            cta_cobro = st.selectbox("Cuenta Cobro", st.session_state.cuentas_ui)
            cta_ingreso = st.selectbox("Cuenta Ingreso", st.session_state.cuentas_ui)
            iva = st.checkbox("IVA 13%", True)
            if iva: cta_iva = st.selectbox("Cuenta IVA", st.session_state.cuentas_ui)
        
        with col_tot:
            monto_iva = subtotal * 0.13 if iva else 0
            total = subtotal + monto_iva
            st.metric("Total", f"${total:,.2f}")
            
        if st.button("💾 Guardar", type="primary", use_container_width=True):
            detalles = [
                {"id_cuenta": st.session_state.mapa_cuentas[cta_cobro]['id_cuenta'], "debe": total, "haber": 0},
                {"id_cuenta": st.session_state.mapa_cuentas[cta_ingreso]['id_cuenta'], "debe": 0, "haber": subtotal}
            ]
            if iva:
                detalles.append({"id_cuenta": st.session_state.mapa_cuentas[cta_iva]['id_cuenta'], "debe": 0, "haber": monto_iva})
            
            payload = {
                "fecha": str(fecha), 
                "descripcion": f"Venta a {cliente} - {len(st.session_state.carrito_items)} items", 
                "tipo": "VENTA", 
                "detalles": detalles
            }
            try:
                requests.post(f"{API_URL}/partidas", json=payload)
                st.success("Guardado!"); st.session_state.carrito_items = []; st.rerun()
            except: st.error("Error conexión")

# --- TAB 2: HISTORIAL ---
with tab_historial:
    if st.button("Actualizar"): st.rerun()
    ventas = obtener_historial_ventas()
    if ventas:
        resumen = [{"ID": v['id_partida'], "Fecha": v['fecha'], "Desc": v['descripcion']} for v in ventas]
        df_h = pd.DataFrame(resumen).sort_values("ID", ascending=False)
        st.dataframe(df_h, use_container_width=True, hide_index=True)
        
        sel_id = st.selectbox("Seleccionar ID para Descarga", df_h['ID'].unique())
        if sel_id:
            v_obj = next(v for v in ventas if v['id_partida'] == sel_id)
            
            c_json, c_pdf = st.columns(2)
            with c_json:
                st.download_button("JSON", json.dumps(v_obj, indent=2), f"f_{sel_id}.json", "application/json")
            with c_pdf:
                if TIENE_FPDF:
                    pdf_data = generar_pdf_factura(v_obj)
                    if pdf_data:
                        st.download_button("PDF", pdf_data, f"f_{sel_id}.pdf", "application/pdf")
                else:
                    st.caption("PDF no disponible")