"""Gráfico 2: Tabla dinámica interactiva con filtros y sumatorias."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import filtros_fecha, COLORS


def render(df):
    st.markdown("## 📊 Tabla Dinámica Interactiva")

    for moneda, emoji, sym in [("SOLES", "🇵🇪", "S/"), ("DOLARES", "🇺🇸", "$")]:
        st.markdown(f"### {emoji} Análisis Dinámico — {moneda}")
        dfm = df[df["Moneda"] == moneda].copy()
        if dfm.empty:
            st.warning(f"No hay datos para {moneda}")
            continue

        with st.expander(f"🔧 Filtros — {moneda}", expanded=True):
            dfm = filtros_fecha(dfm, f"g2_{moneda}")
            # Filtro Genérico
            genericos = sorted(dfm["GENÉRICO"].dropna().unique())
            sel_gen = st.multiselect(
                "🏷️ Genérico",
                genericos,
                default=genericos,
                key=f"g2_{moneda}_gen",
            )
            dfm = dfm[dfm["GENÉRICO"].isin(sel_gen)]
            # Filtro Descripción
            descripciones = sorted(dfm["DESCRIPCION"].dropna().unique())
            sel_desc = st.multiselect(
                "📝 Descripción (opcional)",
                descripciones,
                default=[],
                key=f"g2_{moneda}_desc",
            )
            if sel_desc:
                dfm = dfm[dfm["DESCRIPCION"].isin(sel_desc)]

        if dfm.empty:
            st.info("Sin datos con los filtros seleccionados.")
            continue

        # ── Toggle escala logarítmica ─────────────────────────────────
        use_log = st.toggle(
            "📐 Escala logarítmica",
            value=True,
            key=f"g2_log_{moneda}",
        )
        yaxis_type = "log" if use_log else "linear"

        # ── Sumatorias ────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        total = dfm["CARGO_ABONO"].sum()
        ing = dfm[dfm["TIPO"] == "Ingreso"]["CARGO_ABONO"].sum()
        egr = dfm[dfm["TIPO"] == "Egreso"]["CARGO_ABONO"].sum()
        count = len(dfm)
        c1.metric("💰 Total Neto", f"{sym} {total:,.2f}")
        c2.metric("📥 Ingresos", f"{sym} {ing:,.2f}")
        c3.metric("📤 Egresos", f"{sym} {egr:,.2f}")
        c4.metric("📝 Movimientos", f"{count:,}")

        # ── Sumatoria por Genérico ────────────────────────────────────
        st.markdown("#### Por Genérico")
        gen_pivot = (
            dfm.pivot_table(
                values="CARGO_ABONO",
                index="GENÉRICO",
                columns="TIPO",
                aggfunc="sum",
                fill_value=0,
                margins=True,
                margins_name="TOTAL",
            )
            .reset_index()
        )
        st.dataframe(
            gen_pivot.style.format(
                {c: "{:,.2f}" for c in gen_pivot.columns if c != "GENÉRICO"}
            ),
            use_container_width=True,
        )

        # Gráfico barras por genérico
        gen_data = (
            dfm.groupby(["GENÉRICO", "TIPO"])["CARGO_ABONO"]
            .sum()
            .abs()
            .reset_index()
        )
        if not gen_data.empty:
            fig_bar = px.bar(
                gen_data,
                x="GENÉRICO",
                y="CARGO_ABONO",
                color="TIPO",
                barmode="group",
                template="plotly_dark",
                color_discrete_map={
                    "Ingreso": COLORS["ingreso"],
                    "Egreso": COLORS["egreso"],
                },
                title=f"Cargo/Abono por Genérico — {moneda}",
            )
            fig_bar.update_layout(
                xaxis_tickangle=-45,
                height=450,
                yaxis_type=yaxis_type,
                yaxis_title=f"Monto ({sym})",
            )
            st.plotly_chart(
                fig_bar, use_container_width=True, key=f"bar_g2_{moneda}"
            )

        # ── Sumatoria por Fecha (mensual) ─────────────────────────────
        st.markdown("#### Por Mes")
        dfm["AnoMes"] = dfm["FECHA_OPER_"].dt.to_period("M").astype(str)
        mes_pivot = (
            dfm.pivot_table(
                values="CARGO_ABONO",
                index="AnoMes",
                columns="TIPO",
                aggfunc="sum",
                fill_value=0,
                margins=True,
                margins_name="TOTAL",
            )
            .reset_index()
        )
        st.dataframe(
            mes_pivot.style.format(
                {c: "{:,.2f}" for c in mes_pivot.columns if c != "AnoMes"}
            ),
            use_container_width=True,
        )

        # Gráfico líneas mensual
        mes_data = (
            dfm.groupby(["AnoMes", "TIPO"])["CARGO_ABONO"]
            .sum()
            .abs()
            .reset_index()
        )
        if not mes_data.empty:
            fig_line = px.line(
                mes_data,
                x="AnoMes",
                y="CARGO_ABONO",
                color="TIPO",
                markers=True,
                template="plotly_dark",
                color_discrete_map={
                    "Ingreso": COLORS["ingreso"],
                    "Egreso": COLORS["egreso"],
                },
                title=f"Evolución Mensual — {moneda}",
            )
            fig_line.update_layout(
                height=400,
                yaxis_type=yaxis_type,
                yaxis_title=f"Monto ({sym})",
            )
            st.plotly_chart(
                fig_line, use_container_width=True, key=f"line_g2_{moneda}"
            )

        # ── Tabla detallada ───────────────────────────────────────────
        with st.expander(f"📋 Detalle completo — {moneda}"):
            show = dfm[
                [
                    "FECHA_OPER_",
                    "DESCRIPCION",
                    "GENÉRICO",
                    "TIPO",
                    "CARGO_ABONO",
                    "SALDO_CONTABLE",
                ]
            ].copy()
            show["FECHA_OPER_"] = show["FECHA_OPER_"].dt.strftime("%d/%m/%Y")
            st.dataframe(show, use_container_width=True, height=400)

        st.divider()
