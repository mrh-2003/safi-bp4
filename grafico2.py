"""Gráfico 2: Tabla dinámica interactiva con filtros, sumatorias y gráficos espejo."""
import streamlit as st
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

        # Preparar datos mensuales para los gráficos espejo
        dfm["AnoMes"] = dfm["FECHA_OPER_"].dt.to_period("M").astype(str)
        ing_mes = (
            dfm[dfm["TIPO"] == "Ingreso"]
            .groupby("AnoMes")["CARGO_ABONO"]
            .sum()
            .abs()
        )
        egr_mes = (
            dfm[dfm["TIPO"] == "Egreso"]
            .groupby("AnoMes")["CARGO_ABONO"]
            .sum()
            .abs()
        )
        all_months = sorted(set(ing_mes.index) | set(egr_mes.index))
        ing_vals = [ing_mes.get(m, 0) for m in all_months]
        egr_vals = [-egr_mes.get(m, 0) for m in all_months]  # negativo para espejo

        # ── 1. Gráfico espejo mensual (Barras) ─────────────────────────
        st.markdown("#### 🪞 Ingresos vs Egresos (espejo mensual)")
        fig_mirror = go.Figure()
        fig_mirror.add_trace(
            go.Bar(
                x=all_months,
                y=ing_vals,
                name="Ingresos",
                marker_color=COLORS["ingreso"],
                hovertemplate="%{x}<br>Ingreso: %{y:,.2f}<extra></extra>",
            )
        )
        fig_mirror.add_trace(
            go.Bar(
                x=all_months,
                y=egr_vals,
                name="Egresos",
                marker_color=COLORS["egreso"],
                hovertemplate="%{x}<br>Egreso: %{customdata:,.2f}<extra></extra>",
                customdata=[abs(v) for v in egr_vals],
            )
        )
        # Línea neta
        net_vals = [i + e for i, e in zip(ing_vals, egr_vals)]
        fig_mirror.add_trace(
            go.Scatter(
                x=all_months,
                y=net_vals,
                name="Neto",
                mode="lines+markers",
                line=dict(color="#FFD93D", width=2, dash="dot"),
                marker=dict(size=6),
                hovertemplate="%{x}<br>Neto: %{y:,.2f}<extra></extra>",
            )
        )
        fig_mirror.add_hline(
            y=0, line_width=1, line_color="rgba(255,255,255,0.4)"
        )
        fig_mirror.update_layout(
            template="plotly_dark",
            title=f"Espejo Ingresos (+) vs Egresos (−) — {moneda}",
            xaxis_title="Mes",
            yaxis_title=f"Monto ({sym})",
            barmode="relative",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12),
            height=480,
        )
        st.plotly_chart(
            fig_mirror, use_container_width=True, key=f"mirror_g2_{moneda}"
        )

        # ── Sumatoria por Genérico (Tabla) ─────────────────────────────
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

        # ── 2. Gráfico espejo por Genérico (Barras) ─────────────────────
        st.markdown("#### 🪞 Cargo/Abono por Genérico (espejo)")
        gen_ing = (
            dfm[dfm["TIPO"] == "Ingreso"]
            .groupby("GENÉRICO")["CARGO_ABONO"]
            .sum()
            .abs()
        )
        gen_egr = (
            dfm[dfm["TIPO"] == "Egreso"]
            .groupby("GENÉRICO")["CARGO_ABONO"]
            .sum()
            .abs()
        )

        all_genericos = sorted(set(gen_ing.index) | set(gen_egr.index))
        gen_ing_vals = [gen_ing.get(g, 0) for g in all_genericos]
        gen_egr_vals = [-gen_egr.get(g, 0) for g in all_genericos]  # negativo

        fig_gen_mirror = go.Figure()
        fig_gen_mirror.add_trace(
            go.Bar(
                x=all_genericos,
                y=gen_ing_vals,
                name="Ingresos",
                marker_color=COLORS["ingreso"],
                hovertemplate="%{x}<br>Ingreso: %{y:,.2f}<extra></extra>",
            )
        )
        fig_gen_mirror.add_trace(
            go.Bar(
                x=all_genericos,
                y=gen_egr_vals,
                name="Egresos",
                marker_color=COLORS["egreso"],
                hovertemplate="%{x}<br>Egreso: %{customdata:,.2f}<extra></extra>",
                customdata=[abs(v) for v in gen_egr_vals],
            )
        )
        # Neto line
        gen_net_vals = [i + e for i, e in zip(gen_ing_vals, gen_egr_vals)]
        fig_gen_mirror.add_trace(
            go.Scatter(
                x=all_genericos,
                y=gen_net_vals,
                name="Neto",
                mode="lines+markers",
                line=dict(color="#FFD93D", width=2, dash="dot"),
                marker=dict(size=6),
                hovertemplate="%{x}<br>Neto: %{y:,.2f}<extra></extra>",
            )
        )
        fig_gen_mirror.add_hline(
            y=0, line_width=1, line_color="rgba(255,255,255,0.4)"
        )
        fig_gen_mirror.update_layout(
            template="plotly_dark",
            title=f"Espejo por Genérico — {moneda}",
            xaxis_title="Genérico",
            yaxis_title=f"Monto ({sym})",
            barmode="relative",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12),
            height=500,
        )
        fig_gen_mirror.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(
            fig_gen_mirror,
            use_container_width=True,
            key=f"bar_g2_mirror_{moneda}",
        )

        # ── Sumatoria por Fecha (Tabla) ────────────────────────────────
        st.markdown("#### Por Mes")
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

        # ── 3. Gráfico espejo de Evolución Mensual (Líneas) ──────────────
        st.markdown("#### 🪞 Evolución Mensual (espejo)")
        fig_line_mirror = go.Figure()
        fig_line_mirror.add_trace(
            go.Scatter(
                x=all_months,
                y=ing_vals,
                name="Ingresos",
                mode="lines+markers",
                line=dict(color=COLORS["ingreso"], width=3),
                marker=dict(size=6),
                hovertemplate="%{x}<br>Ingreso: %{y:,.2f}<extra></extra>",
            )
        )
        fig_line_mirror.add_trace(
            go.Scatter(
                x=all_months,
                y=egr_vals,
                name="Egresos",
                mode="lines+markers",
                line=dict(color=COLORS["egreso"], width=3),
                marker=dict(size=6),
                hovertemplate="%{x}<br>Egreso: %{customdata:,.2f}<extra></extra>",
                customdata=[abs(v) for v in egr_vals],
            )
        )
        fig_line_mirror.add_trace(
            go.Scatter(
                x=all_months,
                y=net_vals,
                name="Neto",
                mode="lines+markers",
                line=dict(color="#FFD93D", width=2, dash="dot"),
                marker=dict(size=6),
                hovertemplate="%{x}<br>Neto: %{y:,.2f}<extra></extra>",
            )
        )
        fig_line_mirror.add_hline(
            y=0, line_width=1, line_color="rgba(255,255,255,0.4)"
        )
        fig_line_mirror.update_layout(
            template="plotly_dark",
            title=f"Evolución Mensual Espejo — {moneda}",
            xaxis_title="Mes",
            yaxis_title=f"Monto ({sym})",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12),
            height=450,
        )
        st.plotly_chart(
            fig_line_mirror,
            use_container_width=True,
            key=f"line_g2_mirror_{moneda}",
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
