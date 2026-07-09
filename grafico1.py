"""Gráfico 1: Líneas de Ingresos vs Egresos por SALDO_CONTABLE (Soles y Dólares)."""
import streamlit as st
import plotly.graph_objects as go
from utils import filtros_fecha, filtro_generico, COLORS


def render(df):
    st.markdown("## 📈 Saldo Contable — Ingresos vs Egresos")

    for moneda, emoji, sym in [("SOLES", "🇵🇪", "S/"), ("DOLARES", "🇺🇸", "$")]:
        st.markdown(f"### {emoji} {moneda}")
        dfm = df[df["Moneda"] == moneda].copy()
        if dfm.empty:
            st.warning(f"No hay datos para {moneda}")
            continue

        with st.expander(f"🔧 Filtros — {moneda}", expanded=True):
            dfm = filtros_fecha(dfm, f"g1_{moneda}")
            dfm = filtro_generico(dfm, f"g1_{moneda}")

        if dfm.empty:
            st.info("Sin datos con los filtros seleccionados.")
            continue

        # ── Toggle escala logarítmica ─────────────────────────────────
        use_log = st.toggle(
            "📐 Escala logarítmica",
            value=True,
            key=f"g1_log_{moneda}",
        )

        ingresos = dfm[dfm["TIPO"] == "Ingreso"].copy()
        egresos = dfm[dfm["TIPO"] == "Egreso"].copy()

        ing_group = (
            ingresos.groupby(ingresos["FECHA_OPER_"].dt.date)["SALDO_CONTABLE"]
            .last()
            .sort_index()
        )
        egr_group = (
            egresos.groupby(egresos["FECHA_OPER_"].dt.date)["SALDO_CONTABLE"]
            .last()
            .sort_index()
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=list(ing_group.index),
                y=list(ing_group.values),
                mode="lines+markers",
                name="Ingresos",
                line=dict(color=COLORS["ingreso"], width=2),
                marker=dict(size=4),
                hovertemplate="Fecha: %{x}<br>Saldo: %{y:,.2f}<extra>Ingreso</extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=list(egr_group.index),
                y=list(egr_group.values),
                mode="lines+markers",
                name="Egresos",
                line=dict(color=COLORS["egreso"], width=2),
                marker=dict(size=4),
                hovertemplate="Fecha: %{x}<br>Saldo: %{y:,.2f}<extra>Egreso</extra>",
            )
        )
        yaxis_type = "log" if use_log else "linear"
        fig.update_layout(
            template="plotly_dark",
            title=f"Saldo Contable — {moneda}",
            xaxis_title="Fecha",
            yaxis_title=f"Saldo Contable ({sym})",
            yaxis_type=yaxis_type,
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12),
            height=480,
        )
        st.plotly_chart(fig, use_container_width=True, key=f"chart1_{moneda}")

        # Tabla
        with st.expander(f"📋 Tabla de datos — {moneda}"):
            tabla = dfm[
                [
                    "FECHA_OPER_",
                    "TIPO",
                    "DESCRIPCION",
                    "GENÉRICO",
                    "CARGO_ABONO",
                    "SALDO_CONTABLE",
                ]
            ].copy()
            tabla["FECHA_OPER_"] = tabla["FECHA_OPER_"].dt.strftime("%d/%m/%Y")
            st.dataframe(tabla, use_container_width=True, height=400)

        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Ingresos", f"{sym} {ingresos['CARGO_ABONO'].sum():,.2f}")
        c2.metric("Total Egresos", f"{sym} {egresos['CARGO_ABONO'].sum():,.2f}")
        c3.metric("Neto", f"{sym} {dfm['CARGO_ABONO'].sum():,.2f}")
        st.divider()
