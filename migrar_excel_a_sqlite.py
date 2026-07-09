#!/usr/bin/env python3
"""
migrar_excel_a_sqlite.py
========================
Migra los datos del archivo Excel (output.xlsx, hoja "Data") a una base de datos
SQLite (movimientos.db) sin modificar los valores originales.

Reglas de tipos:
  - Las columnas que NO tienen decimales se guardan como INTEGER (no float).
  - Las columnas de fecha se almacenan como TEXT en formato dd/mm/yyyy.
  - Las columnas numéricas con decimales se guardan como REAL.
  - El resto se guarda como TEXT.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────────────────────
ARCHIVO_EXCEL = Path(__file__).resolve().parent.parent / "consolidado_mov_reporte.xlsx"
HOJA = "Data"
DB_PATH = Path(__file__).resolve().parent / "movimientos.db"
TABLA = "movimientos"

# Columnas que son fechas (serán convertidas a dd/mm/yyyy)
COLUMNAS_FECHA = ["FECHA_OPER_", "FECHA_VALOR"]

# Columnas numéricas con decimales → REAL
COLUMNAS_REAL = [
    "CARGO_ABONO",
    "ITF",
    "SALDO_CONTABLE",
    "Valor Tipo Cambio",
    "Monto USD",
]

# Columnas que DEBEN ser enteras → INTEGER (sin decimales, sin .0)
COLUMNAS_ENTERAS = [
    "Nn_OPER_",
]

# Todo lo demás → TEXT


def detectar_tipo_sqlite(col_name: str) -> str:
    """Retorna el tipo SQLite según la clasificación de la columna."""
    if col_name in COLUMNAS_FECHA:
        return "TEXT"
    if col_name in COLUMNAS_REAL:
        return "REAL"
    if col_name in COLUMNAS_ENTERAS:
        return "INTEGER"
    return "TEXT"


def sanitizar_nombre_columna(nombre: str) -> str:
    """Limpia el nombre de columna para que sea compatible con SQLite."""
    # Reemplazar caracteres problemáticos
    nombre = nombre.replace(".", "_").replace(" ", "_")
    # Quitar acentos u otros caracteres especiales si es necesario
    return nombre


def main():
    # ── 1. Leer el archivo Excel ──────────────────────────────────────────
    if not ARCHIVO_EXCEL.exists():
        print(f"❌ No se encontró el archivo: {ARCHIVO_EXCEL}")
        sys.exit(1)

    print(f"📖 Leyendo {ARCHIVO_EXCEL.name} (hoja: {HOJA})...")
    df = pd.read_excel(
        ARCHIVO_EXCEL,
        sheet_name=HOJA,
        dtype=object,  # Leer todo como objeto para no perder datos
    )

    print(f"   → {len(df):,} filas, {len(df.columns)} columnas leídas.")

    # ── 2. Mapear nombres de columnas ─────────────────────────────────────
    # Mantener un mapeo de nombre original → nombre limpio
    col_map = {}
    for col in df.columns:
        nuevo = sanitizar_nombre_columna(col)
        col_map[col] = nuevo

    df.rename(columns=col_map, inplace=True)

    # Actualizar las listas de columnas con los nombres limpios
    columnas_fecha = [sanitizar_nombre_columna(c) for c in COLUMNAS_FECHA]
    columnas_real = [sanitizar_nombre_columna(c) for c in COLUMNAS_REAL]
    columnas_enteras = [sanitizar_nombre_columna(c) for c in COLUMNAS_ENTERAS]

    # ── 3. Transformar tipos ──────────────────────────────────────────────

    # 3a. Fechas → dd/mm/yyyy
    for col in columnas_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y")
            # Los NaT se convierten en NaN por strftime, los dejamos como None
            df[col] = df[col].where(df[col].notna(), None)
            print(f"   📅 {col} → formato dd/mm/yyyy")

    # 3b. Columnas enteras → int (sin .0)
    for col in columnas_enteras:
        if col in df.columns:
            # Convertir a numérico, luego a Int64 (nullable integer)
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].astype("Int64")  # Nullable integer de pandas
            print(f"   🔢 {col} → INTEGER")

    # 3c. Columnas REAL → float
    for col in columnas_real:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            print(f"   💲 {col} → REAL")

    # 3d. El resto de columnas → TEXT (ya son object/str)
    for col in df.columns:
        if col not in columnas_fecha + columnas_real + columnas_enteras:
            # Convertir a string, reemplazar 'nan' por None
            df[col] = df[col].astype(str)
            df[col] = df[col].replace({"nan": None, "None": None, "": None})

    # ── 4. Crear la base de datos SQLite ──────────────────────────────────
    print(f"\n💾 Creando base de datos: {DB_PATH.name}")

    # Eliminar la DB si ya existe (migración limpia)
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("   ⚠️  Base de datos anterior eliminada.")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Construir CREATE TABLE con tipos explícitos
    col_defs = []
    for col in df.columns:
        original_name = [k for k, v in col_map.items() if v == col]
        original = original_name[0] if original_name else col
        tipo = detectar_tipo_sqlite(original)
        col_defs.append(f'    "{col}" {tipo}')

    create_sql = f'CREATE TABLE "{TABLA}" (\n'
    create_sql += ",\n".join(col_defs)
    create_sql += "\n);"

    print(f"\n📋 SQL de creación:\n{create_sql}\n")
    cursor.execute(create_sql)

    # ── 5. Insertar datos ─────────────────────────────────────────────────
    placeholders = ", ".join(["?"] * len(df.columns))
    col_names = ", ".join([f'"{c}"' for c in df.columns])
    insert_sql = f'INSERT INTO "{TABLA}" ({col_names}) VALUES ({placeholders})'

    # Convertir DataFrame a lista de tuplas, manejando tipos correctamente
    registros = []
    for _, row in df.iterrows():
        fila = []
        for col in df.columns:
            val = row[col]
            if val is None or (isinstance(val, float) and np.isnan(val)):
                fila.append(None)
            elif col in columnas_enteras:
                # Asegurar que sea int, no float
                if pd.notna(val):
                    fila.append(int(val))
                else:
                    fila.append(None)
            elif col in columnas_real:
                if pd.notna(val):
                    fila.append(float(val))
                else:
                    fila.append(None)
            else:
                fila.append(str(val) if val is not None else None)
        registros.append(tuple(fila))

    cursor.executemany(insert_sql, registros)
    conn.commit()

    print(f"✅ {len(registros):,} registros insertados en la tabla '{TABLA}'.")

    # ── 6. Verificación ──────────────────────────────────────────────────
    cursor.execute(f'SELECT COUNT(*) FROM "{TABLA}"')
    total = cursor.fetchone()[0]
    print(f"🔍 Verificación: {total:,} registros en la tabla.")

    # Mostrar una muestra
    cursor.execute(f'SELECT * FROM "{TABLA}" LIMIT 3')
    muestra = cursor.fetchall()
    print("\n📊 Muestra de los primeros 3 registros:")
    for i, reg in enumerate(muestra, 1):
        print(f"   Registro {i}: {reg}")

    # Verificar tipos
    cursor.execute(f'PRAGMA table_info("{TABLA}")')
    info = cursor.fetchall()
    print("\n📋 Estructura de la tabla:")
    for col_info in info:
        print(f"   {col_info[1]:30s} → {col_info[2]}")

    conn.close()
    print(f"\n🎉 Migración completada exitosamente → {DB_PATH}")


if __name__ == "__main__":
    main()
