"""Limpia la ENAHO: une miembros (módulo 02) con sumaria (módulo 34) y valida contra la pobreza oficial del INEI.

Uso:
    uv run limpiar.py --anio 2024

Entradas:  datos/<anio>/sumaria-<anio>.dta y datos/<anio>/enaho01-<anio>-200.dta
Salidas:   salidas/personas_<anio>.parquet y salidas/validacion.txt
Sale con código 1 si alguna validación falla (igual escribe validacion.txt).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]

# Pobreza monetaria oficial del INEI (% de personas). Fuente: INEI, Evolución de la Pobreza Monetaria
POBREZA_OFICIAL = {
    2024: 27.6,
    2023: 29.0,
    2022: 27.5,
    2021: 25.9,
    2020: 30.1,
    2019: 20.2,
    2018: 20.5,
    2017: 21.7,
    2016: 20.7,
    2015: 21.8,
}
RESIDENTES_ESPERADOS = {2024: 108_664}
TOLERANCIA = 0.1  # puntos porcentuales

COLS_MIEMBROS = LLAVES_PERSONA + [
    "ubigeo", "dominio", "estrato", "p203", "p204", "p205", "p206", "p207", "p208a", "facpob07",
]
COLS_SUMARIA = LLAVES_HOGAR + ["pobreza", "mieperho", "factor07", "gashog2d", "inghog2d", "linea", "linpe"]


def leer(ruta: Path) -> pd.DataFrame:
    """Paso 1 y 2: lee el .dta con códigos (no etiquetas), llaves como texto y nombres normalizados."""
    if not ruta.exists():
        sys.exit(f"ERROR: falta {ruta}. Usa primero la skill descargando-enaho.")
    df = pd.read_stata(ruta, convert_categoricals=False)
    df.columns = [c.lower().replace("ñ", "ni") for c in df.columns]  # «aÑo» -> anio
    for c in LLAVES_PERSONA + ["ubigeo"]:
        if c in df:
            df[c] = df[c].astype(str).str.strip()
    return df


def ponderada(valores: pd.Series, pesos: pd.Series) -> float:
    return float((valores * pesos).sum() / pesos.sum() * 100)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--anio", type=int, default=2024)
    p.add_argument("--datos", type=Path, default=Path("datos"))
    p.add_argument("--salidas", type=Path, default=Path("salidas"))
    a = p.parse_args()
    carpeta = a.datos / str(a.anio)

    # 1-2. Leer y normalizar
    sumaria = leer(carpeta / f"sumaria-{a.anio}.dta")
    miembros = leer(carpeta / f"enaho01-{a.anio}-200.dta")
    filas_modulo = len(miembros)

    # 3. Residentes habituales (definición INEI): miembros no ausentes 30+ días o no miembros presentes 30+ días
    residente = ((miembros.p204 == 1) & (miembros.p205 == 2)) | ((miembros.p204 == 2) & (miembros.p206 == 1))
    personas = miembros.loc[residente, COLS_MIEMBROS].copy()

    # 4. Unir cada persona con su hogar; validate="m:1" falla si la sumaria tuviera hogares repetidos
    base = personas.merge(sumaria[COLS_SUMARIA], on=LLAVES_HOGAR, how="left", validate="m:1")

    # 5. Construir variables
    base["anio"] = a.anio
    base["departamento"] = base.ubigeo.str[:2]
    base["urbano"] = base.estrato <= 5
    base["area"] = base.urbano.map({True: "Urbana", False: "Rural"})
    base["pobre"] = base.pobreza <= 2
    base["pobre_extremo"] = base.pobreza == 1
    base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
    base["edad"] = base.p208a
    base["grupo_edad"] = pd.cut(
        base.edad, bins=[-1, 13, 17, 29, 44, 59, 200],
        labels=["0-13", "14-17", "18-29", "30-44", "45-59", "60+"],
    ).astype(str)

    # 6. Validar
    w_hogar = sumaria.factor07 * sumaria.mieperho
    pob_sumaria = ponderada(sumaria.pobreza <= 2, w_hogar)
    ext_sumaria = ponderada(sumaria.pobreza == 1, w_hogar)
    pob_personas = ponderada(base.pobre, base.facpob07)
    oficial = POBREZA_OFICIAL.get(a.anio)

    chequeos = [
        ("Llaves de persona únicas", not personas.duplicated(LLAVES_PERSONA).any()),
        ("Llaves de hogar únicas en sumaria", not sumaria.duplicated(LLAVES_HOGAR).any()),
        ("La unión no perdió ni duplicó filas", len(base) == len(personas)),
        ("Toda persona tiene hogar en la sumaria", base.pobreza.notna().all()),
        ("ubigeo con 6 dígitos (ceros conservados)", base.ubigeo.str.fullmatch(r"\d{6}").all()),
        ("25 departamentos", base.departamento.nunique() == 25),
    ]
    if a.anio in RESIDENTES_ESPERADOS:
        chequeos.append((f"Residentes = {RESIDENTES_ESPERADOS[a.anio]:,}", len(base) == RESIDENTES_ESPERADOS[a.anio]))
    if oficial is not None:
        chequeos.append((f"Pobreza replica INEI ({oficial} %) ± {TOLERANCIA}", abs(pob_sumaria - oficial) < TOLERANCIA))

    ok = all(r for _, r in chequeos)
    lineas = [
        f"VALIDACIÓN ENAHO {a.anio}",
        f"Estado: {'OK' if ok else 'FALLÓ'}",
        "",
        f"Filas módulo 200:              {filas_modulo:,}",
        f"Residentes habituales (base):  {len(base):,}",
        f"Hogares en sumaria:            {len(sumaria):,}",
        f"Población expandida:           {base.facpob07.sum():,.0f}",
        "",
        f"Pobreza oficial INEI:          {oficial if oficial is not None else 'sin dato'} %",
        f"Pobreza (sumaria, factor07×mieperho): {pob_sumaria:.2f} %",
        f"Pobreza extrema (sumaria):     {ext_sumaria:.2f} %",
        f"Pobreza (base personas, facpob07):    {pob_personas:.2f} %",
        "",
    ] + [f"[{'OK' if r else 'X '}] {n}" for n, r in chequeos]

    # 7. Guardar
    a.salidas.mkdir(parents=True, exist_ok=True)
    salida = a.salidas / f"personas_{a.anio}.parquet"
    base.to_parquet(salida, index=False)
    (a.salidas / "validacion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    print(f"\nBase guardada en {salida}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
