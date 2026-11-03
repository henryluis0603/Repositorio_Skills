"""Descarga módulos de la ENAHO (STATA) del portal de microdatos del INEI y el GeoJSON departamental.

Uso:
    uv run descargar.py --anio 2024
    uv run descargar.py --anio 2023 --modulos 34 02 05
    uv run descargar.py --listar
"""

import argparse
import hashlib
import sys
import urllib.request
import zipfile
from pathlib import Path

# Código de la encuesta en el portal del INEI (ENAHO metodología actualizada, anual)
CODIGOS = {
    2024: 966,
    2023: 906,
    2022: 784,
    2021: 759,
    2020: 737,
    2019: 687,
    2018: 634,
    2017: 603,
    2016: 546,
    2015: 498,
}

URL_INEI = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{codigo}-Modulo{modulo}.zip"
URL_GEOJSON = (
    "https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/"
    "sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson"
)

MODULOS_BASE = ["34", "02"]  # sumaria y miembros del hogar: lo que usa limpiando-enaho


def bajar(url: str, destino: Path) -> None:
    """Descarga url a destino; si ya existe y no está vacío, no la vuelve a bajar."""
    if destino.exists() and destino.stat().st_size > 0:
        print(f"  ya existe: {destino}")
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(destino.suffix + ".part")
    peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(peticion, timeout=120) as respuesta, open(temporal, "wb") as f:
        while bloque := respuesta.read(1 << 20):
            f.write(bloque)
    temporal.rename(destino)
    print(f"  bajado:    {destino} ({destino.stat().st_size / 1e6:.1f} MB)")


def extraer(zip_path: Path, carpeta: Path) -> list[Path]:
    """Extrae solo los .dta y .pdf del zip, aplanando subcarpetas. Rechaza rutas fuera de carpeta."""
    carpeta.mkdir(parents=True, exist_ok=True)
    extraidos = []
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip() is not None:
            raise SystemExit(f"ERROR: {zip_path} está corrupto; bórralo y vuelve a correr")
        for info in z.infolist():
            nombre = Path(info.filename).name
            if info.is_dir() or not nombre.lower().endswith((".dta", ".pdf")):
                continue
            destino = carpeta / nombre.lower()
            if not destino.exists():
                with z.open(info) as origen, open(destino, "wb") as f:
                    f.write(origen.read())
            extraidos.append(destino)
    return extraidos


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--anio", type=int, default=2024)
    p.add_argument("--modulos", nargs="+", default=MODULOS_BASE, help="Números de módulo, p. ej. 34 02 05")
    p.add_argument("--datos", type=Path, default=Path("datos"))
    p.add_argument("--sin-geojson", action="store_true")
    p.add_argument("--listar", action="store_true", help="Muestra los años disponibles y sale")
    a = p.parse_args()

    if a.listar:
        for anio, codigo in CODIGOS.items():
            print(f"{anio}: código {codigo}")
        return

    if a.anio not in CODIGOS:
        sys.exit(f"ERROR: no tengo el código del INEI para {a.anio}. Años: {sorted(CODIGOS)}")
    codigo = CODIGOS[a.anio]
    carpeta = a.datos / str(a.anio)
    print(f"ENAHO {a.anio} (código INEI {codigo}) -> {carpeta}/")

    for modulo in a.modulos:
        modulo = modulo.zfill(2)
        zip_path = a.datos / f"{codigo}-Modulo{modulo}.zip"
        try:
            bajar(URL_INEI.format(codigo=codigo, modulo=modulo), zip_path)
        except Exception as e:  # noqa: BLE001 - se reporta y se sigue con el resto
            print(f"  ERROR módulo {modulo}: {e}")
            continue
        for archivo in extraer(zip_path, carpeta):
            sha = hashlib.sha256(archivo.read_bytes()).hexdigest()[:12]
            print(f"  extraído:  {archivo} (sha256 {sha})")

    if not a.sin_geojson:
        bajar(URL_GEOJSON, a.datos / "peru_departamental_simple.geojson")

    print("Listo.")


if __name__ == "__main__":
    main()
