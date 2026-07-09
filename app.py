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

    # ── Toggle global de escala ───────────────────────────────────
    use_log = st.toggle(
        "📐 Escala logarítmica",
        value=False,
        key="global_log_scale",
        help="Aplica escala logarítmica a todos los gráficos de barras y líneas.",
    )
    st.session_state["yaxis_type"] = "log" if use_log else "linear"

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

    st.markdown("---")
    st.markdown("### ⚙️ Configuración del Resumen")
    cc1, cc2 = st.columns(2)
    with cc1:
        moneda_sel = st.radio(
            "🪙 Moneda a considerar",
            ["Todos", "SOLES", "DOLARES"],
            index=0,
            horizontal=True,
            key="resumen_moneda_radio"
        )
    with cc2:
        metrica_sel = st.radio(
            "📊 Métrica de los gráficos",
            ["Monto", "Cantidad"],
            index=0,
            horizontal=True,
            key="resumen_metrica_radio"
        )

    # Filtrar datos
    df_res = df.copy()
    if moneda_sel != "Todos":
        df_res = df_res[df_res["Moneda"] == moneda_sel]

    df_res["MontoAbs"] = df_res["CARGO_ABONO"].abs()

    st.markdown("### Distribución de Movimientos")
    import plotly.express as px

    col1, col2 = st.columns(2)
    with col1:
        if metrica_sel == "Monto":
            fig_tipo = px.pie(
                df_res, names="TIPO", values="MontoAbs",
                title="Por Tipo (Monto Absoluto)", template="plotly_dark",
                color_discrete_sequence=["#00C9A7", "#FF6B6B"], hole=0.4
            )
        else:
            fig_tipo = px.pie(
                df_res, names="TIPO",
                title="Por Tipo (Cantidad de Movimientos)", template="plotly_dark",
                color_discrete_sequence=["#00C9A7", "#FF6B6B"], hole=0.4
            )
        st.plotly_chart(fig_tipo, use_container_width=True, key="pie_tipo_resumen")

    with col2:
        if metrica_sel == "Monto":
            fig_mon = px.pie(
                df_res, names="Moneda", values="MontoAbs",
                title="Por Moneda (Monto Absoluto)", template="plotly_dark",
                color_discrete_sequence=["#FFD93D", "#6ECCAF"], hole=0.4
            )
        else:
            fig_mon = px.pie(
                df_res, names="Moneda",
                title="Por Moneda (Cantidad de Movimientos)", template="plotly_dark",
                color_discrete_sequence=["#FFD93D", "#6ECCAF"], hole=0.4
            )
        st.plotly_chart(fig_mon, use_container_width=True, key="pie_moneda_resumen")

    # Top genéricos
    st.markdown("### Top Genéricos")
    top_gen = df_res.groupby("GENÉRICO")["CARGO_ABONO"].agg(
        monto_total=lambda x: x.abs().sum(),
        cantidad="count"
    ).reset_index()

    if metrica_sel == "Monto":
        top_gen = top_gen.sort_values("monto_total", ascending=False)
        fig_top = px.bar(
            top_gen, x="GENÉRICO", y="monto_total", color="cantidad",
            template="plotly_dark",
            title=f"Monto Total por Genérico ({moneda_sel})",
            color_continuous_scale="Viridis",
            labels={"monto_total": "Monto Total (Absoluto)", "cantidad": "Cantidad", "GENÉRICO": "Genérico"}
        )
    else:
        top_gen = top_gen.sort_values("cantidad", ascending=False)
        fig_top = px.bar(
            top_gen, x="GENÉRICO", y="cantidad", color="monto_total",
            template="plotly_dark",
            title=f"Cantidad de Movimientos por Genérico ({moneda_sel})",
            color_continuous_scale="Viridis",
            labels={"cantidad": "Cantidad de Movimientos", "monto_total": "Monto Total (Absoluto)", "GENÉRICO": "Genérico"}
        )

    fig_top.update_layout(
        xaxis_tickangle=-45, height=450,
        yaxis_type=st.session_state.get("yaxis_type", "linear"),
    )
    st.plotly_chart(fig_top, use_container_width=True, key="bar_top_genericos")

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
