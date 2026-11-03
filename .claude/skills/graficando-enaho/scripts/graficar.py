"""Grafica un indicador de pobreza de la ENAHO por grupo, con reglas fijas de diseño.

Uso:
    uv run graficar.py --por area
    uv run graficar.py --por sexo --indicador pobre_extremo --anio 2024
    uv run graficar.py --por grupo_edad --filtro "area == 'Rural'"

Entrada: salidas/personas_<anio>.parquet (la crea la skill limpiando-enaho)
Salida:  figuras/<indicador>_<por>_<anio>.png y la tabla impresa en pantalla
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

COLOR = "#1f4e79"  # un solo color para todas las barras
GRUPOS = {
    "area": "área de residencia",
    "sexo": "sexo",
    "grupo_edad": "grupo de edad",
    "departamento": "departamento",
}
INDICADORES = {"pobre": "Pobreza monetaria", "pobre_extremo": "Pobreza extrema"}
# Orden natural; los grupos que no aparecen aquí se ordenan de mayor a menor
ORDEN_FIJO = {"grupo_edad": ["0-13", "14-17", "18-29", "30-44", "45-59", "60+"]}
# Nombre de cada departamento según los dos primeros dígitos del ubigeo (INEI)
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
    "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco",
    "11": "Ica", "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima",
    "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura",
    "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--por", choices=GRUPOS, required=True)
    p.add_argument("--indicador", choices=INDICADORES, default="pobre")
    p.add_argument("--anio", type=int, default=2024)
    p.add_argument("--filtro", help="Expresión de pandas.query, p. ej. \"sexo == 'Mujer'\"")
    p.add_argument("--salidas", type=Path, default=Path("salidas"))
    p.add_argument("--figuras", type=Path, default=Path("figuras"))
    a = p.parse_args()

    ruta = a.salidas / f"personas_{a.anio}.parquet"
    if not ruta.exists():
        sys.exit(f"ERROR: falta {ruta}. Usa primero la skill limpiando-enaho.")
    base = pd.read_parquet(ruta)
    if a.filtro:
        base = base.query(a.filtro)

    # Siempre ponderado con facpob07: es un % de personas, no de encuestas
    base = base.assign(_num=base[a.indicador] * base.facpob07)
    tabla = base.groupby(a.por).agg(num=("_num", "sum"), pob=("facpob07", "sum"), n=("facpob07", "size"))
    tabla["pct"] = (tabla.num / tabla.pob * 100).astype(float)
    if a.por in ORDEN_FIJO:
        tabla = tabla.reindex([g for g in ORDEN_FIJO[a.por] if g in tabla.index])
    else:
        tabla = tabla.sort_values("pct", ascending=False)
    if a.por == "departamento":
        tabla.index = tabla.index.map(DEPARTAMENTOS)

    titulo = f"{INDICADORES[a.indicador]} por {GRUPOS[a.por]}, Perú {a.anio}"
    if a.filtro:
        titulo += f" ({a.filtro})"

    alto = max(3.5, 0.35 * len(tabla) + 1.5)
    fig, ax = plt.subplots(figsize=(8, alto))
    etiquetas = tabla.index.astype(str)
    barras = ax.barh(etiquetas, tabla.pct, color=COLOR)
    ax.invert_yaxis()  # el primero arriba
    ax.set_xlim(0, max(tabla.pct.max() * 1.15, 1))  # siempre desde cero
    ax.bar_label(barras, labels=[f"{v:.1f} %" for v in tabla.pct], padding=3, fontsize=9)
    ax.set_xlabel("% de personas")
    ax.set_title(titulo, loc="left", fontsize=12, fontweight="bold")
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.text(0.01, 0.01, f"Fuente: INEI, ENAHO {a.anio}. Ponderado con facpob07.", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    a.figuras.mkdir(parents=True, exist_ok=True)
    salida = a.figuras / f"{a.indicador}_{a.por}_{a.anio}.png"
    fig.savefig(salida, dpi=200)

    print(titulo)
    print(tabla[["pct", "n"]].rename(columns={"pct": "%", "n": "encuestados"}).round(1).to_string())
    print(f"\nFigura guardada en {salida}")


if __name__ == "__main__":
    main()
