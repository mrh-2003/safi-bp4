"""Utilidades compartidas para la app Streamlit."""
import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "movimientos.db"

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


@st.cache_data(ttl=300)
def cargar_datos():
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql("SELECT * FROM movimientos", conn)
    conn.close()
    df["FECHA_OPER_"] = pd.to_datetime(df["FECHA_OPER_"], format="%d/%m/%Y", errors="coerce")
    df["FECHA_VALOR"] = pd.to_datetime(df["FECHA_VALOR"], format="%d/%m/%Y", errors="coerce")
    df["Anio"] = df["FECHA_OPER_"].dt.year
    df["Mes"] = df["FECHA_OPER_"].dt.month
    df["MesNombre"] = df["Mes"].map(MESES_ES)
    return df


def filtros_fecha(df, key_prefix):
    """Renderiza filtros de fecha agrupados por año → meses, y retorna df filtrado."""
    anios = sorted(df["Anio"].dropna().unique().astype(int))

    # ── Selector de años ──────────────────────────────────────────────
    sel_anios = st.multiselect(
        "📅 Años", anios, default=anios, key=f"{key_prefix}_anio"
    )

    if not sel_anios:
        return df.iloc[0:0]  # vacío

    # ── Selector de meses POR CADA AÑO seleccionado ───────────────────
    meses_seleccionados = {}
    cols = st.columns(len(sel_anios))
    for i, anio in enumerate(sorted(sel_anios)):
        with cols[i]:
            meses_disp = sorted(
                df[df["Anio"] == anio]["Mes"].dropna().unique().astype(int)
            )
            opciones = [f"{MESES_ES[m]}" for m in meses_disp]
            sel = st.multiselect(
                f"Meses {anio}",
                options=meses_disp,
                default=meses_disp,
                format_func=lambda x: MESES_ES[x],
                key=f"{key_prefix}_mes_{anio}",
            )
            meses_seleccionados[anio] = sel

    # ── Rango de fechas (opcional, superpuesto) ───────────────────────
    fechas_validas = df["FECHA_OPER_"].dropna()
    if len(fechas_validas) > 0:
        rango = st.date_input(
            "🗓️ Rango de fechas (opcional)",
            value=(fechas_validas.min(), fechas_validas.max()),
            key=f"{key_prefix}_rng",
        )
    else:
        rango = None

    # ── Aplicar filtros ───────────────────────────────────────────────
    mask = pd.Series(False, index=df.index)
    for anio, meses in meses_seleccionados.items():
        mask |= (df["Anio"] == anio) & (df["Mes"].isin(meses))

    filtrado = df[mask]

    if rango and len(rango) == 2:
        filtrado = filtrado[
            (filtrado["FECHA_OPER_"].dt.date >= rango[0])
            & (filtrado["FECHA_OPER_"].dt.date <= rango[1])
        ]

    return filtrado


def filtro_generico(df, key_prefix):
    genericos = sorted(df["GENÉRICO"].dropna().unique())
    sel = st.multiselect(
        "🏷️ Filtrar por Genérico",
        genericos,
        default=genericos,
        key=f"{key_prefix}_gen",
    )
    return df[df["GENÉRICO"].isin(sel)]


COLORS = {
    "ingreso": "#00C9A7",
    "egreso": "#FF6B6B",
    "soles": "#FFD93D",
    "dolares": "#6ECCAF",
    "bg": "#0E1117",
    "card": "#1a1a2e",
    "text": "#FAFAFA",
    "accent1": "#00D2FF",
    "accent2": "#FF4ECD",
}
