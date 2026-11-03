"""Mapa de un indicador de pobreza de la ENAHO por departamento, unido por código.

Uso:
    uv run mapear.py
    uv run mapear.py --indicador pobre_extremo --anio 2024

Entradas: salidas/personas_<anio>.parquet (skill limpiando-enaho)
          datos/peru_departamental_simple.geojson (skill descargando-enaho)
Salida:   mapas/<nombre>_departamento.png y la tabla impresa en pantalla
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

INDICADORES = {"pobre": ("pobreza", "Pobreza monetaria"), "pobre_extremo": ("pobreza_extrema", "Pobreza extrema")}
# Referencias INEI 2024 (sumaria, factor07 × mieperho). Con facpob07 difieren hasta ~0.5 puntos
REFERENCIA_2024 = {"06": 45.0, "16": 43.0, "21": 39.9, "11": 6.0, "18": 11.0, "17": 11.1}
TOLERANCIA = 0.6


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--indicador", choices=INDICADORES, default="pobre")
    p.add_argument("--anio", type=int, default=2024)
    p.add_argument("--salidas", type=Path, default=Path("salidas"))
    p.add_argument("--geojson", type=Path, default=Path("datos/peru_departamental_simple.geojson"))
    p.add_argument("--mapas", type=Path, default=Path("mapas"))
    a = p.parse_args()

    ruta = a.salidas / f"personas_{a.anio}.parquet"
    if not ruta.exists():
        sys.exit(f"ERROR: falta {ruta}. Usa primero la skill limpiando-enaho.")
    if not a.geojson.exists():
        sys.exit(f"ERROR: falta {a.geojson}. Usa primero la skill descargando-enaho.")

    base = pd.read_parquet(ruta)
    base = base.assign(_num=base[a.indicador] * base.facpob07)
    tabla = base.groupby("departamento").agg(num=("_num", "sum"), pob=("facpob07", "sum"))
    tabla["pct"] = (tabla.num / tabla.pob * 100).astype(float)

    # Unir por código, nunca por nombre: ubigeo[:2] con FIRST_IDDP (Lima 15 y Callao 07 van separados)
    geo = gpd.read_file(a.geojson)
    geo["FIRST_IDDP"] = geo.FIRST_IDDP.astype(str).str.zfill(2)
    mapa = geo.merge(tabla, left_on="FIRST_IDDP", right_index=True, how="left", validate="1:1")

    sin_dato = mapa.loc[mapa.pct.isna(), "NOMBDEP"].tolist()
    assert len(mapa) == 25, f"Se esperaban 25 departamentos y hay {len(mapa)}"
    assert not sin_dato, f"Departamentos sin dato (la unión falló): {sin_dato}"
    if a.anio == 2024 and a.indicador == "pobre":
        for cod, ref in REFERENCIA_2024.items():
            valor = tabla.loc[cod, "pct"]
            assert abs(valor - ref) < TOLERANCIA, f"Departamento {cod}: {valor:.1f} % vs referencia {ref} %"

    nombre, etiqueta = INDICADORES[a.indicador]
    fig, ax = plt.subplots(figsize=(7, 9))
    # Un solo tono de claro a oscuro, desde 0; nunca arcoíris
    mapa.plot(
        column="pct", cmap="Reds", vmin=0, vmax=mapa.pct.max(), linewidth=0.4, edgecolor="white", ax=ax,
        legend=True, legend_kwds={"label": "% de personas", "shrink": 0.5},
    )
    ax.set_axis_off()
    ax.set_title(f"{etiqueta} por departamento, Perú {a.anio}", loc="left", fontsize=13, fontweight="bold")
    fig.text(0.02, 0.02, f"Fuente: INEI, ENAHO {a.anio}. Ponderado con facpob07.", fontsize=8, color="#555555")

    a.mapas.mkdir(parents=True, exist_ok=True)
    salida = a.mapas / f"{nombre}_departamento.png"
    fig.savefig(salida, dpi=200, bbox_inches="tight")

    orden = mapa.sort_values("pct", ascending=False)[["FIRST_IDDP", "NOMBDEP", "pct"]]
    print(f"{etiqueta} por departamento, {a.anio} — 25 de 25 con dato")
    print(orden.rename(columns={"FIRST_IDDP": "cod", "NOMBDEP": "departamento", "pct": "%"}).round(1).to_string(index=False))
    print(f"\nMapa guardado en {salida}")


if __name__ == "__main__":
    main()
