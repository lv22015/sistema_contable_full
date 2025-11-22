import streamlit as st
import requests
import pandas as pd
import os
from datetime import date, datetime

# Intentamos importar utils, si no existen (para pruebas locales), usamos pass
try:
    from utils.auth import require_login
    from utils.sidebar import render_sidebar
    require_login()
    render_sidebar()
except ImportError:
    pass

# Configuración de la API
API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="Mayorización", layout="wide", page_icon="📚")
st.title("📚 Mayorización (Mayor Auxiliar)")
st.markdown("---")

# ==========================================
# FUNCIONES DE DATOS (CON CACHÉ)
# ==========================================

@st.cache_data(ttl=10)  # Cachear por 10 segundos para evitar llamadas excesivas pero mantener datos frescos
def obtener_datos_maestros():
    """
    Obtiene partidas y cuentas, y retorna un DataFrame 'aplanado' listo para analizar.
    """
    # 1. Obtener Cuentas
    cuentas_map = {}
    try:
        r_cuentas = requests.get(f"{API_URL}/cuentas")
        if r_cuentas.status_code == 200:
            datos_cuentas = r_cuentas.json()
        else:
            st.warning(f"⚠️ No se pudo obtener cuentas: {r_cuentas.status_code}")
            datos_cuentas = []
        cuentas_map = {c['id_cuenta']: c for c in datos_cuentas}
    except Exception as e:
        st.error(f"Error conectando con cuentas: {e}")
        return pd.DataFrame(), {}

    # 2. Obtener Partidas
    flat_data = []
    try:
        r_partidas = requests.get(f"{API_URL}/partidas")
        if r_partidas.status_code == 200:
            partidas = r_partidas.json()
        else:
            st.warning(f"⚠️ No se pudo obtener partidas: {r_partidas.status_code}")
            partidas = []

        # APLANAR DATOS (Flattening)
        # Convertimos la estructura anidada JSON en una tabla plana inmediatamente
        for p in partidas:
            fecha_dt = datetime.strptime(p['fecha'], "%Y-%m-%d").date()
            for d in p.get('detalles', []):
                cta = cuentas_map.get(d['id_cuenta'], {})
                flat_data.append({
                    "id_partida": p['id_partida'],
                    "fecha": fecha_dt,
                    "desc_partida": p['descripcion'],
                    "tipo": p['tipo'],
                    "id_cuenta": d['id_cuenta'],
                    "codigo": cta.get('codigo', 'S/C'),
                    "cuenta": cta.get('nombre', 'Desconocida'),
                    "debe": float(d.get('debe', 0.0)),
                    "haber": float(d.get('haber', 0.0))
                })

    except Exception as e:
        st.error(f"Error procesando partidas: {e}")
        return pd.DataFrame(), {}

    return pd.DataFrame(flat_data), cuentas_map

# ==========================================
# INTERFAZ Y LÓGICA
# ==========================================

# 1. Cargar Datos
with st.spinner("Cargando partidas y cuentas..."):
    # Botón para forzar actualización
    col_refresh1, col_refresh2 = st.columns([4, 1])
    with col_refresh2:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    df_master, map_cuentas = obtener_datos_maestros()

if df_master.empty:
    st.warning("No hay datos disponibles o hubo un error de conexión.")
    st.stop()

# 2. Filtros
with st.expander("🔍 Filtros de Mayorización", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        # Validar que hay datos antes de obtener min/max
        fecha_min = df_master['fecha'].min() if not df_master.empty else date.today()
        f_inicio = st.date_input("Desde", value=fecha_min)
    with c2:
        fecha_max = df_master['fecha'].max() if not df_master.empty else date.today()
        f_fin = st.date_input("Hasta", value=fecha_max)
    with c3:
        tipos_disp = ["Todos"] + list(df_master['tipo'].unique()) if not df_master.empty else ["Todos"]
        f_tipo = st.selectbox("Tipo de Partida", tipos_disp)
    with c4:
        # Filtro opcional por cuenta específica desde el inicio
        if not df_master.empty:
            cuentas_disp = ["Todas"] + sorted([f"{c['codigo']} - {c['nombre']}" for c in map_cuentas.values()])
        else:
            cuentas_disp = ["Todas"]
        f_cuenta = st.selectbox("Filtrar Cuenta", cuentas_disp)

# 3. Aplicar Filtros al DataFrame
if not df_master.empty:
    mask = (df_master['fecha'] >= f_inicio) & (df_master['fecha'] <= f_fin)
    if f_tipo != "Todos":
        mask = mask & (df_master['tipo'] == f_tipo)
    if f_cuenta != "Todas":
        # Extraer código de forma segura
        try:
            cod_filtro = f_cuenta.split(" - ")[0]
            mask = mask & (df_master['codigo'] == cod_filtro)
        except:
            st.warning("⚠️ Error al procesar filtro de cuenta.")
    
    df_filtered = df_master.loc[mask].copy()
else:
    df_filtered = pd.DataFrame()

# ==========================================
# VISTA 1: BALANCE DE COMPROBACIÓN (RESUMEN)
# ==========================================
st.subheader("📊 Resumen de Saldos")

if df_filtered.empty:
    st.info("No hay movimientos con los filtros seleccionados.")
else:
    # Agrupación potente con Pandas (reemplaza los bucles manuales)
    # Agrupamos por Código y Nombre, sumamos Debe y Haber
    df_resumen = df_filtered.groupby(['codigo', 'cuenta'])[['debe', 'haber']].sum().reset_index()
    
    # Agregar tipo de cuenta al resumen para cálculo correcto de saldo
    def obtener_tipo_cuenta(codigo):
        for id_c, c_data in map_cuentas.items():
            if c_data.get('codigo') == codigo:
                return c_data.get('tipo', 'ACTIVO').upper()
        return 'ACTIVO'
    
    df_resumen['tipo_cuenta'] = df_resumen['codigo'].apply(obtener_tipo_cuenta)
    
    # Calculamos Saldo considerando naturaleza contable
    # DEUDORA (ACTIVO, GASTO): Saldo = Debe - Haber
    # ACREEDORA (PASIVO, INGRESO, CAPITAL): Saldo = Haber - Debe
    def calcular_saldo(row):
        if row['tipo_cuenta'] in ['ACTIVO', 'GASTO']:
            return row['debe'] - row['haber']
        else:
            return row['haber'] - row['debe']
    
    df_resumen['saldo'] = df_resumen.apply(calcular_saldo, axis=1)
    
    # Mostrar solo las columnas relevantes
    df_mostrar = df_resumen[['codigo', 'cuenta', 'tipo_cuenta', 'debe', 'haber', 'saldo']]
    df_mostrar.columns = ['Código', 'Cuenta', 'Tipo', 'Debe', 'Haber', 'Saldo']

    st.dataframe(
        df_mostrar,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Código": "Código",
            "Cuenta": "Cuenta",
            "Tipo": "Tipo",
            "Debe": st.column_config.NumberColumn("Total Debe", format="$ %.2f"),
            "Haber": st.column_config.NumberColumn("Total Haber", format="$ %.2f"),
            "Saldo": st.column_config.NumberColumn("Saldo Neto", format="$ %.2f"),
        }
    )

    # Totales de control (Footer)
    t_debe = df_resumen['debe'].sum()
    t_haber = df_resumen['haber'].sum()
    diff = t_debe - t_haber
    
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Suma Debe", f"${t_debe:,.2f}")
    col_t2.metric("Suma Haber", f"${t_haber:,.2f}")
    col_t3.metric("Cuadre", "✅ OK" if abs(diff) < 0.01 else f"❌ ${diff:,.2f}", delta_color="off" if abs(diff) < 0.01 else "inverse")

# ==========================================
# VISTA 2: MAYOR AUXILIAR DETALLADO (Running Balance)
# ==========================================
st.markdown("---")
st.subheader("🔎 Detalle por Cuenta (Libro Mayor)")

# Selector dinámico basado en lo que quedó filtrado
lista_cuentas_activas = df_filtered['cuenta'].unique()
cuenta_sel = st.selectbox("Seleccione Cuenta para ver detalles:", sorted(lista_cuentas_activas))

if cuenta_sel:
    # Filtramos solo esa cuenta y ORDENAMOS por fecha (Crucial para saldo acumulado)
    df_detalle = df_filtered[df_filtered['cuenta'] == cuenta_sel].sort_values(by=['fecha', 'id_partida'])
    
    # Obtener tipo de cuenta para calcular saldo correctamente
    cuenta_detalle = None
    for id_c, c_data in map_cuentas.items():
        if c_data.get('nombre') == cuenta_sel:
            cuenta_detalle = c_data
            break
    
    # CÁLCULO DE SALDO ACUMULADO (RUNNING BALANCE)
    # Considerar naturaleza de la cuenta:
    # - DEUDORA (ACTIVO, GASTO): Saldo = Debe - Haber
    # - ACREEDORA (PASIVO, INGRESO, CAPITAL): Saldo = Haber - Debe
    es_deudora = cuenta_detalle.get('tipo', 'ACTIVO') if cuenta_detalle else True
    es_deudora = es_deudora.upper() in ['ACTIVO', 'GASTO'] if isinstance(es_deudora, str) else True
    
    if es_deudora:
        # Cuentas deudoras: Debe positivo, Haber negativo
        df_detalle['mov_neto'] = df_detalle['debe'] - df_detalle['haber']
    else:
        # Cuentas acreedoras: Haber positivo, Debe negativo
        df_detalle['mov_neto'] = df_detalle['haber'] - df_detalle['debe']
    
    df_detalle['saldo_acumulado'] = df_detalle['mov_neto'].cumsum()

    # Métricas de cabecera
    saldo_actual = df_detalle['saldo_acumulado'].iloc[-1]
    naturaleza = "DEUDORA" if es_deudora else "ACREEDORA"
    m_c1, m_c2, m_c3 = st.columns([2, 1, 1])
    m_c1.info(f"Movimientos de: **{cuenta_sel}**")
    m_c2.metric("Naturaleza", naturaleza)
    m_c3.metric("Saldo al cierre", f"${saldo_actual:,.2f}")

    # Tabla detallada
    st.dataframe(
        df_detalle[['fecha', 'tipo', 'desc_partida', 'debe', 'haber', 'saldo_acumulado']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "fecha": st.column_config.DateColumn("Fecha"),
            "tipo": "Tipo",
            "desc_partida": "Concepto",
            "debe": st.column_config.NumberColumn("Debe", format="$ %.2f"),
            "haber": st.column_config.NumberColumn("Haber", format="$ %.2f"),
            "saldo_acumulado": st.column_config.NumberColumn(
                "Saldo Acumulado", 
                format="$ %.2f",
                help="Saldo de la cuenta después de este movimiento"
            ),
        }
    )
    
    # GRAFICO DE TENDENCIA
    st.markdown("##### Evolución del Saldo")
    st.line_chart(df_detalle, x='fecha', y='saldo_acumulado')

    # Exportación individual
    csv = df_detalle.to_csv(index=False)
    st.download_button(
        label=f"📥 Descargar Mayor de {cuenta_sel}",
        data=csv,
        file_name=f"mayor_{cuenta_sel}_{date.today()}.csv",
        mime="text/csv"
    )