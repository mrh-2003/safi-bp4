"""Gráfico 3: Diagrama de tubos – Flujo financiero entre cuentas Soles y Dólares."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import filtros_fecha, COLORS


def _build_tube_diagram(dff):
    """Construye el diagrama de dos tubos horizontales con flechas perpendiculares."""

    # ── Clasificar movimientos ────────────────────────────────────────
    es_transf = dff["GENÉRICO"].str.contains(
        "TRANSFERENCIA INTERNA", case=False, na=False
    )

    sol = dff[dff["Moneda"] == "SOLES"]
    dol = dff[dff["Moneda"] == "DOLARES"]

    # Ingresos/Egresos EXTERNOS (sin transferencias internas)
    dol_ing = dol[(dol["TIPO"] == "Ingreso") & ~es_transf[dol.index]]
    dol_egr = dol[(dol["TIPO"] == "Egreso") & ~es_transf[dol.index]]
    sol_ing = sol[(sol["TIPO"] == "Ingreso") & ~es_transf[sol.index]]
    sol_egr = sol[(sol["TIPO"] == "Egreso") & ~es_transf[sol.index]]

    dol_ing_total = abs(dol_ing["CARGO_ABONO"].sum())
    dol_egr_total = abs(dol_egr["CARGO_ABONO"].sum())
    sol_ing_total = abs(sol_ing["CARGO_ABONO"].sum())
    sol_egr_total = abs(sol_egr["CARGO_ABONO"].sum())

    # Transferencias internas
    # "Sale de soles" = SOLES + Egreso + TRANSFERENCIA INTERNA
    transf_sale_sol = abs(
        sol[(sol["TIPO"] == "Egreso") & es_transf[sol.index]]["CARGO_ABONO"].sum()
    )
    # "Entra a dólares" desde soles = DOLARES + Ingreso + TRANSFERENCIA INTERNA
    transf_entra_dol = abs(
        dol[(dol["TIPO"] == "Ingreso") & es_transf[dol.index]]["CARGO_ABONO"].sum()
    )
    # "Sale de dólares" = DOLARES + Egreso + TRANSFERENCIA INTERNA
    transf_sale_dol = abs(
        dol[(dol["TIPO"] == "Egreso") & es_transf[dol.index]]["CARGO_ABONO"].sum()
    )
    # "Entra a soles" desde dólares = SOLES + Ingreso + TRANSFERENCIA INTERNA
    transf_entra_sol = abs(
        sol[(sol["TIPO"] == "Ingreso") & es_transf[sol.index]]["CARGO_ABONO"].sum()
    )

    # Genéricos de ingreso/egreso ordenados por monto (externos)
    gen_ing_dol = (
        dol_ing.groupby("GENÉRICO")["CARGO_ABONO"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )
    gen_egr_dol = (
        dol_egr.groupby("GENÉRICO")["CARGO_ABONO"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )
    gen_ing_sol = (
        sol_ing.groupby("GENÉRICO")["CARGO_ABONO"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )
    gen_egr_sol = (
        sol_egr.groupby("GENÉRICO")["CARGO_ABONO"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )

    # ── Construir figura ──────────────────────────────────────────────
    fig = go.Figure()

    # Parámetros de layout
    # Tubo superior: DOLARES (y = 4.5 centro)  — más separados
    # Tubo inferior: SOLES   (y = 0.5 centro)
    # x: 1 (entrada) → 9 (salida)

    max_flow = max(dol_ing_total, dol_egr_total, sol_ing_total, sol_egr_total, 1)

    def tube_height(amount, min_h=0.25, max_h=0.6):
        return min_h + (max_h - min_h) * (amount / max_flow) if max_flow > 0 else min_h

    # Alturas de los tubos según flujo
    dol_h_in = tube_height(dol_ing_total)
    dol_h_out = tube_height(dol_egr_total)
    sol_h_in = tube_height(sol_ing_total)
    sol_h_out = tube_height(sol_egr_total)

    dol_y = 4.5
    sol_y = 0.5
    gap_top = dol_y - max(dol_h_in, dol_h_out)   # borde inferior del tubo USD
    gap_bot = sol_y + max(sol_h_in, sol_h_out)     # borde superior del tubo PEN
    mid_y = (gap_top + gap_bot) / 2                # centro exacto del espacio libre
    arrow_pad = 0.15                               # separación entre flecha y borde del tubo

    # ── Tubo DÓLARES (azul) ───────────────────────────────────────────
    fig.add_shape(
        type="path",
        path=(
            f"M 1,{dol_y - dol_h_in} "
            f"L 9,{dol_y - dol_h_out} "
            f"L 9,{dol_y + dol_h_out} "
            f"L 1,{dol_y + dol_h_in} Z"
        ),
        fillcolor="rgba(21, 101, 192, 0.55)",
        line=dict(color="#1565C0", width=2),
    )
    fig.add_annotation(
        x=5, y=dol_y,
        text="<b>💵 CUENTA DÓLARES</b>",
        font=dict(size=16, color="white"),
        showarrow=False,
    )

    # ── Tubo SOLES (dorado) ───────────────────────────────────────────
    fig.add_shape(
        type="path",
        path=(
            f"M 1,{sol_y - sol_h_in} "
            f"L 9,{sol_y - sol_h_out} "
            f"L 9,{sol_y + sol_h_out} "
            f"L 1,{sol_y + sol_h_in} Z"
        ),
        fillcolor="rgba(245, 127, 23, 0.55)",
        line=dict(color="#F57F17", width=2),
    )
    fig.add_annotation(
        x=5, y=sol_y,
        text="<b>🪙 CUENTA SOLES</b>",
        font=dict(size=16, color="white"),
        showarrow=False,
    )

    # ── Flechas de ENTRADA (izquierda) ────────────────────────────────
    fig.add_annotation(
        x=1, y=dol_y,
        ax=-1.5, ay=dol_y,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2, arrowsize=1.8, arrowwidth=3,
        arrowcolor="#42A5F5",
    )
    fig.add_annotation(
        x=-0.3, y=dol_y,
        text=f"<b>ENTRA<br>$ {dol_ing_total:,.2f}</b>",
        font=dict(size=13, color="#42A5F5"),
        showarrow=False,
        bgcolor="rgba(21,101,192,0.2)",
        bordercolor="#42A5F5",
        borderwidth=1,
        borderpad=6,
    )

    fig.add_annotation(
        x=1, y=sol_y,
        ax=-1.5, ay=sol_y,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2, arrowsize=1.8, arrowwidth=3,
        arrowcolor="#FFA726",
    )
    fig.add_annotation(
        x=-0.3, y=sol_y,
        text=f"<b>ENTRA<br>S/ {sol_ing_total:,.2f}</b>",
        font=dict(size=13, color="#FFA726"),
        showarrow=False,
        bgcolor="rgba(245,127,23,0.2)",
        bordercolor="#FFA726",
        borderwidth=1,
        borderpad=6,
    )

    # ── Flechas de SALIDA (derecha) ───────────────────────────────────
    fig.add_annotation(
        x=11.5, y=dol_y,
        ax=9, ay=dol_y,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2, arrowsize=1.8, arrowwidth=3,
        arrowcolor="#EF5350",
    )
    fig.add_annotation(
        x=10.3, y=dol_y,
        text=f"<b>SALE<br>$ {dol_egr_total:,.2f}</b>",
        font=dict(size=13, color="#EF5350"),
        showarrow=False,
        bgcolor="rgba(229,57,53,0.2)",
        bordercolor="#EF5350",
        borderwidth=1,
        borderpad=6,
    )

    fig.add_annotation(
        x=11.5, y=sol_y,
        ax=9, ay=sol_y,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2, arrowsize=1.8, arrowwidth=3,
        arrowcolor="#EF5350",
    )
    fig.add_annotation(
        x=10.3, y=sol_y,
        text=f"<b>SALE<br>S/ {sol_egr_total:,.2f}</b>",
        font=dict(size=13, color="#EF5350"),
        showarrow=False,
        bgcolor="rgba(229,57,53,0.2)",
        bordercolor="#EF5350",
        borderwidth=1,
        borderpad=6,
    )

    # ── Flechas perpendiculares (transferencias internas) ─────────────
    # Las flechas van desde el borde del tubo + padding, NO dentro del tubo

    # Flecha: SOLES → DÓLARES (hacia arriba) — x=3.5
    fig.add_annotation(
        x=3.5, y=gap_top - arrow_pad,
        ax=3.5, ay=gap_bot + arrow_pad,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=3, arrowsize=1.5, arrowwidth=3,
        arrowcolor="#66BB6A",
    )
    # Etiqueta SOLES→DÓLARES — centrada en el gap, a la izquierda de la flecha
    fig.add_annotation(
        x=3.2, y=mid_y,
        text=(
            f"<b>SOLES → DÓLARES</b><br>"
            f"Sale: S/ {transf_sale_sol:,.2f}<br>"
            f"Entra: $ {transf_entra_dol:,.2f}"
        ),
        font=dict(size=11, color="#66BB6A"),
        showarrow=False,
        xanchor="right",
        yanchor="middle",
        bgcolor="rgba(102,187,106,0.15)",
        bordercolor="#66BB6A",
        borderwidth=1,
        borderpad=6,
    )

    # Flecha: DÓLARES → SOLES (hacia abajo) — x=6.5
    fig.add_annotation(
        x=6.5, y=gap_bot + arrow_pad,
        ax=6.5, ay=gap_top - arrow_pad,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=3, arrowsize=1.5, arrowwidth=3,
        arrowcolor="#AB47BC",
    )
    # Etiqueta DÓLARES→SOLES — centrada en el gap, a la derecha de la flecha
    fig.add_annotation(
        x=6.8, y=mid_y,
        text=(
            f"<b>DÓLARES → SOLES</b><br>"
            f"Sale: $ {transf_sale_dol:,.2f}<br>"
            f"Entra: S/ {transf_entra_sol:,.2f}"
        ),
        font=dict(size=11, color="#AB47BC"),
        showarrow=False,
        xanchor="left",
        yanchor="middle",
        bgcolor="rgba(171,71,188,0.15)",
        bordercolor="#AB47BC",
        borderwidth=1,
        borderpad=6,
    )

    # ── Etiquetas de Genéricos ────────────────────────────────────────
    def _generico_labels(gen_series, x_pos, y_center, color, sym, side="left"):
        """Agrega etiquetas de genéricos apiladas verticalmente."""
        if gen_series.empty:
            return
        lines = []
        for nombre, monto in gen_series.head(8).items():
            lines.append(f"• {nombre}: {sym} {monto:,.2f}")
        if len(gen_series) > 8:
            lines.append(f"  ... +{len(gen_series) - 8} más")
        text = "<br>".join(lines)
        align = "right" if side == "left" else "left"
        fig.add_annotation(
            x=x_pos,
            y=y_center,
            text=f"<span style='font-size:10px'>{text}</span>",
            font=dict(size=10, color=color),
            showarrow=False,
            xanchor=align,
            yanchor="middle",
            align=align,
        )

    _generico_labels(gen_ing_dol, -1.8, dol_y, "#90CAF9", "$", "left")
    _generico_labels(gen_ing_sol, -1.8, sol_y, "#FFE0B2", "S/", "left")
    _generico_labels(gen_egr_dol, 11.8, dol_y, "#EF9A9A", "$", "right")
    _generico_labels(gen_egr_sol, 11.8, sol_y, "#EF9A9A", "S/", "right")

    # ── Layout final ──────────────────────────────────────────────────
    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text="Flujo Financiero — Cuentas Dólares y Soles",
            font=dict(size=20),
        ),
        xaxis=dict(
            visible=False,
            range=[-4, 14],
        ),
        yaxis=dict(
            visible=False,
            range=[-1, 6],
            scaleanchor="x",
        ),
        height=750,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False,
    )

    return fig


def render(df):
    st.markdown("## 🔄 Flujo Financiero entre Cuentas")
    st.caption(
        "Dos tubos horizontales representan las cuentas en Dólares y Soles. "
        "El grosor varía según el volumen de dinero. Las flechas perpendiculares "
        "muestran las transferencias internas entre ambas cuentas."
    )

    with st.expander("🔧 Filtros de Fecha", expanded=True):
        dff = filtros_fecha(df, "g3_flow")

    if dff.empty:
        st.info("Sin datos con los filtros seleccionados.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────
    es_transf = dff["GENÉRICO"].str.contains(
        "TRANSFERENCIA INTERNA", case=False, na=False
    )
    sol = dff[dff["Moneda"] == "SOLES"]
    dol = dff[dff["Moneda"] == "DOLARES"]

    st.markdown("### 💵 Cuenta Dólares")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Ingresos Terceros",
        f"$ {abs(dol[(dol['TIPO']=='Ingreso') & ~es_transf[dol.index]]['CARGO_ABONO'].sum()):,.2f}",
    )
    c2.metric(
        "Egresos Terceros",
        f"$ {abs(dol[(dol['TIPO']=='Egreso') & ~es_transf[dol.index]]['CARGO_ABONO'].sum()):,.2f}",
    )
    c3.metric(
        "Recibe de Soles",
        f"$ {abs(dol[(dol['TIPO']=='Ingreso') & es_transf[dol.index]]['CARGO_ABONO'].sum()):,.2f}",
    )
    c4.metric(
        "Envía a Soles",
        f"$ {abs(dol[(dol['TIPO']=='Egreso') & es_transf[dol.index]]['CARGO_ABONO'].sum()):,.2f}",
    )

    st.markdown("### 🪙 Cuenta Soles")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric(
        "Ingresos Terceros",
        f"S/ {abs(sol[(sol['TIPO']=='Ingreso') & ~es_transf[sol.index]]['CARGO_ABONO'].sum()):,.2f}",
    )
    c6.metric(
        "Egresos Terceros",
        f"S/ {abs(sol[(sol['TIPO']=='Egreso') & ~es_transf[sol.index]]['CARGO_ABONO'].sum()):,.2f}",
    )
    c7.metric(
        "Recibe de Dólares",
        f"S/ {abs(sol[(sol['TIPO']=='Ingreso') & es_transf[sol.index]]['CARGO_ABONO'].sum()):,.2f}",
    )
    c8.metric(
        "Envía a Dólares",
        f"S/ {abs(sol[(sol['TIPO']=='Egreso') & es_transf[sol.index]]['CARGO_ABONO'].sum()):,.2f}",
    )

    # ── Diagrama de tubos ─────────────────────────────────────────────
    fig = _build_tube_diagram(dff)
    st.plotly_chart(fig, use_container_width=True, key="tube_flow")

    # ── Desglose por Genérico (barras horizontales) ───────────────────
    st.markdown("### 🏷️ Desglose por Genérico (ordenado por monto)")
    st.caption("💡 *Haga clic en una barra para reemplazar el gráfico con el detalle de descripciones. Use el botón para volver.*")

    yaxis_type = st.session_state.get("yaxis_type", "linear")

    for moneda, sym, emoji in [("DOLARES", "$", "💵"), ("SOLES", "S/", "🪙")]:
        st.markdown(f"#### {emoji} {moneda}")
        dfmon = dff[(dff["Moneda"] == moneda) & ~es_transf].copy()
        if dfmon.empty:
            continue

        for tipo, color in [
            ("Ingreso", COLORS["ingreso"]),
            ("Egreso", COLORS["egreso"]),
        ]:
            sub = dfmon[dfmon["TIPO"] == tipo]
            key_name = f"bar_g3_{moneda}_{tipo}"
            state_key = f"selected_gen_{moneda}_{tipo}"

            if state_key not in st.session_state:
                st.session_state[state_key] = None

            # Si no hay selección, mostramos el gráfico de Genéricos
            if not st.session_state[state_key]:
                grp = (
                    sub.groupby("GENÉRICO")["CARGO_ABONO"]
                    .sum()
                    .abs()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                grp.columns = ["Genérico", "Monto"]
                if grp.empty:
                    continue

                fig_bar = go.Figure(
                    go.Bar(
                        y=grp["Genérico"],
                        x=grp["Monto"],
                        orientation="h",
                        marker_color=color,
                        text=[f"{sym} {v:,.2f}" for v in grp["Monto"]],
                        textposition="auto",
                    )
                )
                fig_bar.update_layout(
                    template="plotly_dark",
                    title=f"{tipo}s — {moneda} (por Genérico)",
                    height=max(300, len(grp) * 35),
                    yaxis=dict(autorange="reversed"),
                    xaxis_title=f"Monto ({sym})",
                    xaxis_type=yaxis_type,
                    margin=dict(l=250),
                )
                
                selected_data = st.plotly_chart(
                    fig_bar,
                    use_container_width=True,
                    on_select="rerun",
                    selection_mode="points",
                    key=key_name
                )

                if selected_data:
                    try:
                        if isinstance(selected_data, dict):
                            points = selected_data.get("selection", {}).get("points", [])
                        else:
                            points = getattr(selected_data, "selection", {}).get("points", [])
                        
                        if points:
                            clicked_val = points[0].get("y", None)
                            if clicked_val:
                                st.session_state[state_key] = clicked_val
                                st.rerun()
                    except Exception:
                        pass
            
            # Si hay selección, mostramos el detalle (reemplazando el gráfico)
            else:
                selected_generic = st.session_state[state_key]
                sub_detail = sub[sub["GENÉRICO"] == selected_generic]
                grp_detail = (
                    sub_detail.groupby("DESCRIPCION")["CARGO_ABONO"]
                    .sum()
                    .abs()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                grp_detail.columns = ["Descripción", "Monto"]

                st.markdown(f"🔍 **Detalle de Genérico: `{selected_generic}`** ({tipo}s)")
                
                if not grp_detail.empty:
                    fig_detail = go.Figure(
                        go.Bar(
                            y=grp_detail["Descripción"],
                            x=grp_detail["Monto"],
                            orientation="h",
                            marker_color="#00D2FF",
                            text=[f"{sym} {v:,.2f}" for v in grp_detail["Monto"]],
                            textposition="auto",
                        )
                    )
                    fig_detail.update_layout(
                        template="plotly_dark",
                        title=f"Desglose de {selected_generic} — {tipo}s ({moneda})",
                        height=max(300, len(grp_detail) * 35),
                        yaxis=dict(autorange="reversed"),
                        xaxis_title=f"Monto ({sym})",
                        xaxis_type=yaxis_type,
                        margin=dict(l=250),
                    )
                    st.plotly_chart(
                        fig_detail,
                        use_container_width=True,
                        key=f"detail_g3_{moneda}_{tipo}"
                    )
                else:
                    st.info("No hay detalles disponibles para este Genérico.")

                if st.button("🔙 Volver a Genéricos", key=f"btn_reset_{moneda}_{tipo}"):
                    st.session_state[state_key] = None
                    st.rerun()

        # Tabla
        with st.expander(f"📋 Detalle — {moneda}"):
            show = dfmon[
                ["FECHA_OPER_", "TIPO", "GENÉRICO", "DESCRIPCION", "CARGO_ABONO"]
            ].copy()
            from utils import filtrar_df_estilo_excel
            show_filtrado = filtrar_df_estilo_excel(show, f"g3_tbl_{moneda}", use_expander=False)
            show_filtrado_show = show_filtrado.copy()
            show_filtrado_show["FECHA_OPER_"] = show_filtrado_show["FECHA_OPER_"].dt.strftime("%d/%m/%Y")
            st.dataframe(show_filtrado_show, use_container_width=True, height=350)

    st.divider()

