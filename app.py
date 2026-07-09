"""
App principal Streamlit — Análisis Financiero BCP
Ejecutar: streamlit run app.py
"""
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Análisis Financiero — FONDO BP4",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
[data-testid="stMetricLabel"] { color: #adb5bd; font-size: 0.85rem; }
[data-testid="stMetricValue"] { font-weight: 700; }
div[data-testid="stExpander"] {
    background: rgba(26,26,46,0.6);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
}
.stDivider { opacity: 0.3; }
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
}
h1, h2, h3 { letter-spacing: -0.02em; }
</style>
""", unsafe_allow_html=True)

# ── Verificar DB ──────────────────────────────────────────────────────
DB_PATH = Path(__file__).resolve().parent / "movimientos.db"
if not DB_PATH.exists():
    st.error("⚠️ No se encontró `movimientos.db`. Ejecute primero `python migrar_excel_a_sqlite.py`.")
    st.stop()

# ── Cargar datos ──────────────────────────────────────────────────────
from utils import cargar_datos
df = cargar_datos()

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/BCP_logo.svg/320px-BCP_logo.svg.png", width=180)
    st.markdown("# 💰 Análisis Financiero")
    st.markdown(f"**Titular:** FONDO BP4")
    st.markdown(f"**Registros:** {len(df):,}")
    st.markdown(f"**Período:** {df['FECHA_OPER_'].min().strftime('%d/%m/%Y')} — {df['FECHA_OPER_'].max().strftime('%d/%m/%Y')}")
    st.divider()

    reporte = st.radio(
        "📑 Seleccionar Reporte",
        ["🏠 Resumen General", "📈 Ingresos vs Egresos", "📊 Tabla Dinámica", "🔄 Flujo Financiero", "📦 Todos los Reportes"],
        index=0,
    )
    st.divider()
    st.caption("App desarrollada para análisis de movimientos bancarios")

# ── Páginas ───────────────────────────────────────────────────────────
if reporte == "🏠 Resumen General":
    st.markdown("# 🏠 Resumen General")
    st.markdown("---")

    # KPIs globales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Movimientos", f"{len(df):,}")
    c2.metric("Ingresos", f"{len(df[df['TIPO']=='Ingreso']):,}")
    c3.metric("Egresos", f"{len(df[df['TIPO']=='Egreso']):,}")
    c4.metric("Genéricos", f"{df['GENÉRICO'].nunique()}")

    c5, c6, c7, c8 = st.columns(4)
    dol = df[df["Moneda"] == "DOLARES"]
    sol = df[df["Moneda"] == "SOLES"]
    c5.metric("💵 Ingresos USD", f"$ {dol[dol['TIPO']=='Ingreso']['CARGO_ABONO'].sum():,.2f}")
    c6.metric("💵 Egresos USD", f"$ {dol[dol['TIPO']=='Egreso']['CARGO_ABONO'].sum():,.2f}")
    c7.metric("🪙 Ingresos PEN", f"S/ {sol[sol['TIPO']=='Ingreso']['CARGO_ABONO'].sum():,.2f}")
    c8.metric("🪙 Egresos PEN", f"S/ {sol[sol['TIPO']=='Egreso']['CARGO_ABONO'].sum():,.2f}")

    st.markdown("### Distribución de Movimientos")
    import plotly.express as px

    col1, col2 = st.columns(2)
    with col1:
        fig_tipo = px.pie(df, names="TIPO", title="Por Tipo", template="plotly_dark",
                          color_discrete_sequence=["#00C9A7", "#FF6B6B"], hole=0.4)
        st.plotly_chart(fig_tipo, use_container_width=True)
    with col2:
        fig_mon = px.pie(df, names="Moneda", title="Por Moneda", template="plotly_dark",
                         color_discrete_sequence=["#FFD93D", "#6ECCAF"], hole=0.4)
        st.plotly_chart(fig_mon, use_container_width=True)

    # Top genéricos
    st.markdown("### Top Genéricos por Volumen")
    top_gen = df.groupby("GENÉRICO")["CARGO_ABONO"].agg(["sum", "count"]).reset_index()
    top_gen.columns = ["Genérico", "Monto Total", "Cantidad"]
    top_gen = top_gen.sort_values("Cantidad", ascending=False)
    fig_top = px.bar(top_gen, x="Genérico", y="Cantidad", color="Monto Total",
                     template="plotly_dark", title="Cantidad de movimientos por Genérico",
                     color_continuous_scale="Viridis")
    fig_top.update_layout(xaxis_tickangle=-45, height=450)
    st.plotly_chart(fig_top, use_container_width=True)

elif reporte == "📈 Ingresos vs Egresos":
    import grafico1
    grafico1.render(df)

elif reporte == "📊 Tabla Dinámica":
    import grafico2
    grafico2.render(df)

elif reporte == "🔄 Flujo Financiero":
    import grafico3
    grafico3.render(df)

elif reporte == "📦 Todos los Reportes":
    st.markdown("# 📦 Reporte Completo")
    st.markdown("---")
    import grafico1, grafico2, grafico3
    grafico1.render(df)
    grafico2.render(df)
    grafico3.render(df)
