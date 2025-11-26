import streamlit as st
import requests
import pandas as pd
import os
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Estados Financieros", layout="wide", page_icon="📈")

try:
    from utils.auth import require_login
    from utils.sidebar import render_sidebar
    require_login()
    render_sidebar()
except ImportError:
    pass

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

# ==========================================
# 2. CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=10)
def cargar_datos_financieros():
    """
    Descarga Cuentas y Partidas, y prepara un DataFrame maestro con tipos de cuenta.
    """
    # A. Cuentas
    try:
        r_cuentas = requests.get(f"{API_URL}/cuentas")
        cuentas = r_cuentas.json() if r_cuentas.status_code == 200 else []
        map_cuentas = {c['id_cuenta']: c for c in cuentas}
    except:
        return pd.DataFrame()

    # B. Partidas
    flat_data = []
    try:
        r_partidas = requests.get(f"{API_URL}/partidas")
        partidas = r_partidas.json() if r_partidas.status_code == 200 else []

        for p in partidas:
            try:
                fecha_dt = date.fromisoformat(p['fecha'][:10])
            except:
                continue
            
            for d in p.get('detalles', []):
                cta = map_cuentas.get(d['id_cuenta'], {})
                # Normalizar tipo de cuenta a mayúsculas
                tipo_cta = cta.get('tipo', 'OTROS').upper()
                
                flat_data.append({
                    "fecha": fecha_dt,
                    "id_cuenta": d['id_cuenta'],
                    "codigo": cta.get('codigo', 'S/C'),
                    "cuenta": cta.get('nombre', 'Desconocida'),
                    "tipo_cuenta": tipo_cta, 
                    "debe": float(d.get('debe', 0.0)),
                    "haber": float(d.get('haber', 0.0))
                })
    except:
        return pd.DataFrame()

    return pd.DataFrame(flat_data)

# ==========================================
# 3. INTERFAZ Y FILTROS
# ==========================================
st.title("📈 Estados Financieros")
st.markdown("Generación automática de Balance General y Estado de Resultados.")
st.markdown("---")

# Botón actualizar
if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

df_master = cargar_datos_financieros()

if df_master.empty:
    st.warning("No hay datos contables suficientes para generar reportes.")
    st.stop()

# Filtros de Fecha
with st.expander("📅 Configuración del Periodo", expanded=True):
    col_f1, col_f2 = st.columns(2)
    # Por defecto año actual
    inicio_anio = date(date.today().year, 1, 1)
    fin_anio = date(date.today().year, 12, 31)
    
    with col_f1:
        f_inicio = st.date_input("Fecha Inicio (Para Estado de Resultados)", value=inicio_anio)
    with col_f2:
        f_fin = st.date_input("Fecha Corte (Para Balance General)", value=date.today())

# ==========================================
# 4. LÓGICA DE CÁLCULO
# ==========================================

# A. ESTADO DE RESULTADOS (SOLO MOVIMIENTOS DEL PERIODO)
# Filtramos transacciones dentro del rango exacto
mask_er = (df_master['fecha'] >= f_inicio) & (df_master['fecha'] <= f_fin)
df_er = df_master.loc[mask_er].copy()

# Agrupar por cuenta
resumen_er = df_er.groupby(['tipo_cuenta', 'codigo', 'cuenta'])[['debe', 'haber']].sum().reset_index()

# Calcular Totales por Rubro
def calcular_total_grupo(tipo_buscado):
    # Filtrar rubro
    df_rubro = resumen_er[resumen_er['tipo_cuenta'] == tipo_buscado]
    # Ingresos (Acreedora): Haber - Debe
    if tipo_buscado == 'INGRESOS':
        return df_rubro['haber'].sum() - df_rubro['debe'].sum()
    # Gastos/Costos (Deudora): Debe - Haber
    else:
        return df_rubro['debe'].sum() - df_rubro['haber'].sum()

total_ingresos = calcular_total_grupo('INGRESOS')
total_gastos = calcular_total_grupo('GASTOS')
total_costos = calcular_total_grupo('COSTOS')

# UTILIDAD O PÉRDIDA DEL EJERCICIO
utilidad_neta = total_ingresos - (total_gastos + total_costos)


# B. BALANCE GENERAL (ACUMULADO HISTÓRICO)
# Filtramos todo lo ocurrido hasta la fecha de corte (f_fin), ignorando f_inicio
mask_bg = (df_master['fecha'] <= f_fin)
df_bg = df_master.loc[mask_bg].copy()

resumen_bg = df_bg.groupby(['tipo_cuenta', 'codigo', 'cuenta'])[['debe', 'haber']].sum().reset_index()

# Función para calcular saldo según naturaleza
def calc_saldo_bg(row):
    # Activos: Deudora
    if row['tipo_cuenta'] == 'ACTIVO':
        return row['debe'] - row['haber']
    # Pasivo/Capital: Acreedora
    else:
        return row['haber'] - row['debe']

resumen_bg['saldo_final'] = resumen_bg.apply(calc_saldo_bg, axis=1)

# Totales Balance
total_activo = resumen_bg[resumen_bg['tipo_cuenta'] == 'ACTIVO']['saldo_final'].sum()
total_pasivo = resumen_bg[resumen_bg['tipo_cuenta'] == 'PASIVO']['saldo_final'].sum()
total_capital_social = resumen_bg[resumen_bg['tipo_cuenta'] == 'CAPITAL']['saldo_final'].sum()

# ¡CRUCIAL! Sumamos la utilidad del ejercicio al capital
total_capital_neto = total_capital_social + utilidad_neta
total_pasivo_mas_capital = total_pasivo + total_capital_neto
diferencia_balance = total_activo - total_pasivo_mas_capital


# ==========================================
# 5. VISUALIZACIÓN (TABS)
# ==========================================

tab_er, tab_bg = st.tabs(["📄 Estado de Resultados", "⚖️ Balance General"])

# --- TAB 1: ESTADO DE RESULTADOS ---
with tab_er:
    st.subheader(f"Estado de Resultados ({f_inicio} al {f_fin})")
    
    # Métricas Encabezado
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Ingresos", f"${total_ingresos:,.2f}")
    m2.metric("Total Gastos y Costos", f"${(total_gastos + total_costos):,.2f}")
    
    color_utilidad = "normal" if utilidad_neta >= 0 else "inverse"
    label_utilidad = "Utilidad Neta" if utilidad_neta >= 0 else "Pérdida Neta"
    m3.metric(label_utilidad, f"${utilidad_neta:,.2f}", delta_color=color_utilidad)
    
    st.markdown("### Detalle")
    
    # Mostrar tablas por sección
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.caption("INGRESOS")
        df_show_ing = resumen_er[resumen_er['tipo_cuenta'] == 'INGRESOS'].copy()
        if not df_show_ing.empty:
            df_show_ing['saldo'] = df_show_ing['haber'] - df_show_ing['debe']
            st.dataframe(df_show_ing[['cuenta', 'saldo']], hide_index=True, use_container_width=True)
        else:
            st.info("Sin ingresos en el periodo")

    with col_der:
        st.caption("GASTOS Y COSTOS")
        df_show_gas = resumen_er[resumen_er['tipo_cuenta'].isin(['GASTOS', 'COSTOS'])].copy()
        if not df_show_gas.empty:
            df_show_gas['saldo'] = df_show_gas['debe'] - df_show_gas['haber']
            st.dataframe(df_show_gas[['cuenta', 'saldo']], hide_index=True, use_container_width=True)
        else:
            st.info("Sin gastos en el periodo")

# --- TAB 2: BALANCE GENERAL ---
with tab_bg:
    st.subheader(f"Balance General (Al {f_fin})")
    
    # Ecuación Contable
    st.info(f"💡 Ecuación Contable: Activo = Pasivo + Capital (+ Resultado Ejercicio)")
    
    bm1, bm2, bm3 = st.columns(3)
    bm1.metric("Total Activo", f"${total_activo:,.2f}")
    bm2.metric("Total Pasivo", f"${total_pasivo:,.2f}")
    bm3.metric("Total Capital (Inc. Utilidad)", f"${total_capital_neto:,.2f}")
    
    # Verificación de Cuadre
    if abs(diferencia_balance) < 0.01:
        st.success(f"✅ BALANCE CUADRADO (Diferencia: ${diferencia_balance:,.2f})")
    else:
        st.error(f"❌ DESCUADRE: ${diferencia_balance:,.2f} (Revise sus partidas)")

    st.markdown("---")
    
    # Columnas visuales estilo reporte
    c_activo, c_pasivo = st.columns(2)
    
    with c_activo:
        st.markdown("### 🟢 ACTIVOS")
        df_act = resumen_bg[resumen_bg['tipo_cuenta'] == 'ACTIVO'].copy()
        if not df_act.empty:
            df_act = df_act[df_act['saldo_final'] != 0] # Ocultar ceros
            st.dataframe(
                df_act[['codigo', 'cuenta', 'saldo_final']], 
                hide_index=True, 
                use_container_width=True,
                column_config={"saldo_final": st.column_config.NumberColumn("Monto", format="$ %.2f")}
            )
        st.markdown(f"**TOTAL ACTIVO: ${total_activo:,.2f}**")

    with c_pasivo:
        st.markdown("### 🔴 PASIVO")
        df_pas = resumen_bg[resumen_bg['tipo_cuenta'] == 'PASIVO'].copy()
        if not df_pas.empty:
            df_pas = df_pas[df_pas['saldo_final'] != 0]
            st.dataframe(
                df_pas[['codigo', 'cuenta', 'saldo_final']], 
                hide_index=True, 
                use_container_width=True,
                column_config={"saldo_final": st.column_config.NumberColumn("Monto", format="$ %.2f")}
            )
        st.markdown(f"**TOTAL PASIVO: ${total_pasivo:,.2f}**")
        
        st.write("")
        st.markdown("### 🔵 CAPITAL")
        df_cap = resumen_bg[resumen_bg['tipo_cuenta'] == 'CAPITAL'].copy()
        
        # Inyectamos visualmente la fila de Utilidad del Ejercicio
        fila_utilidad = pd.DataFrame([{
            'codigo': '---', 
            'cuenta': f'RESULTADO DEL EJERCICIO ({f_inicio} a {f_fin})', 
            'saldo_final': utilidad_neta
        }])
        
        df_cap_show = pd.concat([df_cap[['codigo', 'cuenta', 'saldo_final']], fila_utilidad], ignore_index=True)
        
        st.dataframe(
            df_cap_show, 
            hide_index=True, 
            use_container_width=True,
            column_config={"saldo_final": st.column_config.NumberColumn("Monto", format="$ %.2f")}
        )
        st.markdown(f"**TOTAL CAPITAL + UTILIDAD: ${total_capital_neto:,.2f}**")

    st.markdown("---")
    st.markdown(f"#### 🟰 Total Pasivo + Capital: **${total_pasivo_mas_capital:,.2f}**")