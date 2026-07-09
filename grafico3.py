"""Gráfico 3: Diagrama de flujo financiero estilo Sankey entre cuentas Soles/Dólares."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import filtros_fecha, COLORS

def render(df):
    st.markdown("## 🔄 Flujo Financiero entre Cuentas")
    st.caption("Visualización de entradas, salidas y transferencias internas entre cuentas en Soles y Dólares")

    with st.expander("🔧 Filtros de Fecha", expanded=True):
        dff = filtros_fecha(df, "g3_flow")

    if dff.empty:
        st.info("Sin datos con los filtros seleccionados.")
        return

    # ── Calcular flujos ───────────────────────────────────────────────
    sol = dff[dff["Moneda"] == "SOLES"]
    dol = dff[dff["Moneda"] == "DOLARES"]

    # Detectar transferencias internas
    es_transf = dff["GENÉRICO"].str.contains("TRANSFERENCIA INTERNA", case=False, na=False)

    # Dólares
    dol_ing_ext = dol[(dol["TIPO"] == "Ingreso") & ~es_transf[dol.index]]["CARGO_ABONO"].sum()
    dol_egr_ext = dol[(dol["TIPO"] == "Egreso") & ~es_transf[dol.index]]["CARGO_ABONO"].sum()
    dol_ing_transf = dol[(dol["TIPO"] == "Ingreso") & es_transf[dol.index]]["CARGO_ABONO"].sum()
    dol_egr_transf = dol[(dol["TIPO"] == "Egreso") & es_transf[dol.index]]["CARGO_ABONO"].sum()

    # Soles
    sol_ing_ext = sol[(sol["TIPO"] == "Ingreso") & ~es_transf[sol.index]]["CARGO_ABONO"].sum()
    sol_egr_ext = sol[(sol["TIPO"] == "Egreso") & ~es_transf[sol.index]]["CARGO_ABONO"].sum()
    sol_ing_transf = sol[(sol["TIPO"] == "Ingreso") & es_transf[sol.index]]["CARGO_ABONO"].sum()
    sol_egr_transf = sol[(sol["TIPO"] == "Egreso") & es_transf[sol.index]]["CARGO_ABONO"].sum()

    # ── KPIs ──────────────────────────────────────────────────────────
    st.markdown("### 💵 Cuenta Dólares")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos Terceros", f"$ {abs(dol_ing_ext):,.2f}")
    c2.metric("Egresos Terceros", f"$ {abs(dol_egr_ext):,.2f}")
    c3.metric("Recibe de Soles", f"$ {abs(dol_ing_transf):,.2f}")
    c4.metric("Envía a Soles", f"$ {abs(dol_egr_transf):,.2f}")

    st.markdown("### 🪙 Cuenta Soles")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Ingresos Terceros", f"S/ {abs(sol_ing_ext):,.2f}")
    c6.metric("Egresos Terceros", f"S/ {abs(sol_egr_ext):,.2f}")
    c7.metric("Recibe de Dólares", f"S/ {abs(sol_ing_transf):,.2f}")
    c8.metric("Envía a Dólares", f"S/ {abs(sol_egr_transf):,.2f}")

    # ── Sankey Diagram ────────────────────────────────────────────────
    st.markdown("### 🌊 Diagrama de Flujos")

    # Nodos: 0=IngTercerosUSD, 1=CuentaUSD, 2=EgrTercerosUSD,
    #         3=IngTercerosPEN, 4=CuentaPEN, 5=EgrTercerosPEN
    labels = [
        "Ingresos Terceros (USD)",  # 0
        "Cuenta Dólares",            # 1
        "Salidas Terceros (USD)",    # 2
        "Ingresos Terceros (PEN)",   # 3
        "Cuenta Soles",              # 4
        "Salidas Terceros (PEN)",    # 5
    ]
    node_colors = ["#2196F3", "#1565C0", "#E53935", "#FFC107", "#F57F17", "#E53935"]

    source = [0, 1, 3, 4, 1, 4]
    target = [1, 2, 4, 5, 4, 1]
    value = [
        abs(dol_ing_ext),
        abs(dol_egr_ext),
        abs(sol_ing_ext),
        abs(sol_egr_ext),
        abs(dol_egr_transf),
        abs(sol_egr_transf),
    ]
    link_colors = [
        "rgba(33,150,243,0.4)",   # Ing → USD
        "rgba(229,57,53,0.4)",    # USD → Egr
        "rgba(255,193,7,0.4)",    # Ing → PEN
        "rgba(229,57,53,0.4)",    # PEN → Egr
        "rgba(100,181,246,0.3)",  # USD → PEN transf
        "rgba(255,224,130,0.3)",  # PEN → USD transf
    ]
    link_labels = [
        f"Ingresos ext USD: ${abs(dol_ing_ext):,.2f}",
        f"Egresos ext USD: ${abs(dol_egr_ext):,.2f}",
        f"Ingresos ext PEN: S/{abs(sol_ing_ext):,.2f}",
        f"Egresos ext PEN: S/{abs(sol_egr_ext):,.2f}",
        f"Transf USD→PEN: ${abs(dol_egr_transf):,.2f}",
        f"Transf PEN→USD: S/{abs(sol_egr_transf):,.2f}",
    ]

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=30, thickness=25, line=dict(color="white", width=1),
            label=labels, color=node_colors,
        ),
        link=dict(
            source=source, target=target, value=value,
            color=link_colors, label=link_labels,
        ),
    ))
    fig.update_layout(
        template="plotly_dark", title="Flujo de Dinero entre Cuentas",
        height=550, font=dict(size=13),
    )
    st.plotly_chart(fig, use_container_width=True, key="sankey_flow")

    # ── Desglose por Genérico (ordenado) ──────────────────────────────
    st.markdown("### 🏷️ Desglose por Genérico (ordenado por monto)")
    for moneda, sym, emoji in [("DOLARES", "$", "💵"), ("SOLES", "S/", "🪙")]:
        st.markdown(f"#### {emoji} {moneda}")
        dfmon = dff[(dff["Moneda"] == moneda) & ~es_transf].copy()
        if dfmon.empty:
            continue

        for tipo, color in [("Ingreso", COLORS["ingreso"]), ("Egreso", COLORS["egreso"])]:
            sub = dfmon[dfmon["TIPO"] == tipo]
            grp = sub.groupby("GENÉRICO")["CARGO_ABONO"].sum().abs().sort_values(ascending=False).reset_index()
            grp.columns = ["Genérico", "Monto"]
            if grp.empty:
                continue

            fig_bar = go.Figure(go.Bar(
                y=grp["Genérico"], x=grp["Monto"], orientation="h",
                marker_color=color, text=[f"{sym} {v:,.2f}" for v in grp["Monto"]],
                textposition="auto",
            ))
            fig_bar.update_layout(
                template="plotly_dark", title=f"{tipo}s — {moneda} (por Genérico)",
                height=max(300, len(grp) * 35), yaxis=dict(autorange="reversed"),
                xaxis_title="Monto", margin=dict(l=250),
            )
            st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_g3_{moneda}_{tipo}")

        # Tabla
        with st.expander(f"📋 Detalle — {moneda}"):
            show = dfmon[["FECHA_OPER_", "TIPO", "GENÉRICO", "DESCRIPCION", "CARGO_ABONO"]].copy()
            show["FECHA_OPER_"] = show["FECHA_OPER_"].dt.strftime("%d/%m/%Y")
            st.dataframe(show, use_container_width=True, height=350)

    st.divider()
