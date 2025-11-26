import streamlit as st
import requests
import pandas as pd
import os
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Balanza de Comprobación", layout="wide", page_icon="⚖️")

# ==========================================
# 2. IMPORTS DE SEGURIDAD
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

@st.cache_data(ttl=10)
def obtener_datos_completos():
    """
    Obtiene Cuentas y Partidas, retornando dos DataFrames:
    1. df_cuentas: Catálogo de cuentas
    2. df_partidas_flat: Todas las líneas de partidas aplanadas
    """
    # --- A. Obtener Cuentas ---
    cuentas_map = {}
    try:
        r_cuentas = requests.get(f"{API_URL}/cuentas")
        datos_cuentas = r_cuentas.json() if r_cuentas.status_code == 200 else []
        # Convertimos a DF para facilitar merges
        df_cuentas = pd.DataFrame(datos_cuentas)
        if not df_cuentas.empty:
            # Asegurar columnas clave
            if 'tipo' not in df_cuentas.columns: df_cuentas['tipo'] = 'ACTIVO'
            # Mapa rápido para busquedas por ID
            cuentas_map = {c['id_cuenta']: c for c in datos_cuentas}
    except Exception as e:
        st.error(f"Error cargando cuentas: {e}")
        return pd.DataFrame(), pd.DataFrame()

    # --- B. Obtener Partidas ---
    flat_data = []
    try:
        r_partidas = requests.get(f"{API_URL}/partidas")
        partidas = r_partidas.json() if r_partidas.status_code == 200 else []

        for p in partidas:
            # Parsear fecha seguro
            try:
                fecha_dt = date.fromisoformat(p["fecha"][:10])
            except:
                continue
            
            # Aplanar detalles
            for d in p.get("detalles", []):
                cta = cuentas_map.get(d["id_cuenta"], {})
                flat_data.append({
                    "fecha": fecha_dt,
                    "id_cuenta": d["id_cuenta"],
                    "codigo": cta.get("codigo", "S/C"),
                    "cuenta": cta.get("nombre", "Desconocida"),
                    "tipo_cuenta": cta.get("tipo", "ACTIVO"), # Importante para naturaleza
                    "debe": float(d.get("debe", 0.0)),
                    "haber": float(d.get("haber", 0.0))
                })
                
    except Exception as e:
        st.error(f"Error cargando partidas: {e}")
        return pd.DataFrame(), pd.DataFrame()

    return df_cuentas, pd.DataFrame(flat_data)

# ==========================================
# 4. INTERFAZ Y LÓGICA
# ==========================================

st.title("⚖️ Balanza de Comprobación")
st.markdown("---")

# Botón refrescar
col_top1, col_top2 = st.columns([6, 1])
with col_top2:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Cargar datos
with st.spinner("Procesando contabilidad..."):
    df_cuentas, df_movimientos = obtener_datos_completos()

if df_movimientos.empty:
    st.warning("No hay movimientos registrados para generar la balanza.")
    st.stop()

# --- FILTROS ---
with st.expander("📅 Rango de Fechas", expanded=True):
    c1, c2, c3 = st.columns([1, 1, 2])
    # Por defecto: Mes actual
    today = date.today()
    primer_dia_mes = today.replace(day=1)
    
    with c1:
        f_inicio = st.date_input("Fecha Inicio", value=primer_dia_mes)
    with c2:
        f_fin = st.date_input("Fecha Fin", value=today)

# ==========================================
# 5. CÁLCULO DE LA BALANZA (Lógica Núcleo)
# ==========================================

# A. Separar datos: Históricos (Saldo Inicial) vs Periodo
mask_anteriores = df_movimientos['fecha'] < f_inicio
mask_periodo = (df_movimientos['fecha'] >= f_inicio) & (df_movimientos['fecha'] <= f_fin)

df_ant = df_movimientos.loc[mask_anteriores]
df_per = df_movimientos.loc[mask_periodo]

# B. Agrupar saldos anteriores
# Sumamos debe y haber histórico por cuenta
saldos_ant = df_ant.groupby('id_cuenta')[['debe', 'haber']].sum().reset_index()
saldos_ant.rename(columns={'debe': 'debe_ant', 'haber': 'haber_ant'}, inplace=True)

# C. Agrupar movimientos del periodo
movs_per = df_per.groupby('id_cuenta')[['debe', 'haber']].sum().reset_index()
movs_per.rename(columns={'debe': 'debe_per', 'haber': 'haber_per'}, inplace=True)

# D. Unificar todo con el catálogo de cuentas (Master)
# Usamos df_cuentas como base para que aparezcan cuentas incluso si no tienen movs (opcional)
# O usamos un merge de los movimientos encontrados. Usaremos merge de movimientos para no llenar de ceros.
ids_activos = set(saldos_ant['id_cuenta']).union(set(movs_per['id_cuenta']))
df_balanza = pd.DataFrame({'id_cuenta': list(ids_activos)})

# Pegar info de cuentas
df_balanza = df_balanza.merge(df_cuentas[['id_cuenta', 'codigo', 'nombre', 'tipo']], on='id_cuenta', how='left')

# Pegar Saldos Anteriores
df_balanza = df_balanza.merge(saldos_ant, on='id_cuenta', how='left').fillna(0)

# Pegar Movimientos Periodo
df_balanza = df_balanza.merge(movs_per, on='id_cuenta', how='left').fillna(0)

# ==========================================
# 6. CÁLCULO DE SALDOS NETOS
# ==========================================

def procesar_fila(row):
    # 1. Determinar Naturaleza
    tipo = str(row['tipo']).upper()
    es_deudora = tipo in ['ACTIVO', 'GASTO', 'COSTO']
    
    # 2. Calcular Saldo Inicial Neto
    if es_deudora:
        saldo_ini = row['debe_ant'] - row['haber_ant']
    else:
        saldo_ini = row['haber_ant'] - row['debe_ant']
        
    # 3. Calcular Saldo Final
    # Saldo Final = Saldo Inicial + (Debe Periodo - Haber Periodo) [si es deudora]
    if es_deudora:
        saldo_fin = saldo_ini + row['debe_per'] - row['haber_per']
    else:
        saldo_fin = saldo_ini + row['haber_per'] - row['debe_per']
        
    return pd.Series([saldo_ini, saldo_fin])

df_balanza[['saldo_inicial', 'saldo_final']] = df_balanza.apply(procesar_fila, axis=1)

# Ordenar por código contable para presentación
df_balanza.sort_values('codigo', inplace=True)

# Filtrar cuentas que esten en cero absoluto (opcional, para limpiar vista)
df_view = df_balanza[
    (df_balanza['saldo_inicial'] != 0) | 
    (df_balanza['debe_per'] != 0) | 
    (df_balanza['haber_per'] != 0)
].copy()

# ==========================================
# 7. PRESENTACIÓN DE DATOS
# ==========================================

# Estilizar columnas para mostrar
df_display = df_view[[
    'codigo', 'nombre', 'tipo', 
    'saldo_inicial', 
    'debe_per', 'haber_per', 
    'saldo_final'
]]

# Renombrar columnas para la tabla
df_display.columns = [
    'Código', 'Cuenta', 'Naturaleza', 
    'Saldo Anterior', 
    'Mov. Debe', 'Mov. Haber', 
    'Saldo Final'
]

# Tabla Principal
st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Saldo Anterior": st.column_config.NumberColumn(format="$ %.2f"),
        "Mov. Debe": st.column_config.NumberColumn(format="$ %.2f"),
        "Mov. Haber": st.column_config.NumberColumn(format="$ %.2f"),
        "Saldo Final": st.column_config.NumberColumn(format="$ %.2f", help="Saldo al final del periodo seleccionado"),
    }
)

# ==========================================
# 8. TOTALES DE CONTROL (Footer)
# ==========================================
st.markdown("---")

# Sumatorias
sum_saldo_ant = df_view['saldo_inicial'].sum()
sum_debe = df_view['debe_per'].sum()
sum_haber = df_view['haber_per'].sum()
sum_saldo_fin = df_view['saldo_final'].sum()
diff_movimientos = sum_debe - sum_haber

# Mostrar métricas
c1, c2, c3, c4 = st.columns(4)

c1.metric("∑ Saldo Anterior", f"${sum_saldo_ant:,.2f}")
c2.metric("∑ Mov. Debe", f"${sum_debe:,.2f}")
c3.metric("∑ Mov. Haber", f"${sum_haber:,.2f}")

# El saldo final global no tiene por qué ser cero (Activo - Pasivo = Capital), 
# pero la diferencia entre Debe y Haber del periodo SI debe ser cero.
estado = "✅ CUADRADO" if abs(diff_movimientos) < 0.01 else f"❌ DESCUADRE: ${diff_movimientos:,.2f}"
c4.metric("Control Movimientos", estado, delta_color="normal" if abs(diff_movimientos) < 0.01 else "inverse")

# Botón Exportar
csv = df_display.to_csv(index=False)
st.download_button(
    "📥 Descargar Balanza (CSV)",
    data=csv,
    file_name=f"balanza_comprobacion_{f_inicio}_al_{f_fin}.csv",
    mime="text/csv"
)