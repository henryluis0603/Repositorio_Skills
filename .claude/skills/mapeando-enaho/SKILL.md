---
name: mapeando-enaho
description: Hace un mapa coroplético de la pobreza (monetaria o extrema) por departamento del Perú con la ENAHO del INEI, uniendo por código de ubigeo y no por nombre, y guarda un PNG en mapas/. Úsala cuando pidan un mapa, mapear o ver geográficamente la pobreza por departamento o región con la ENAHO.
argument-hint: "[pobre|pobre_extremo]"
allowed-tools: Bash(uv run *)
---

# Mapear la ENAHO

1. Si no existe `salidas/hogares_2024.parquet` (o el del año pedido), usa primero la skill `limpiando-enaho`.
2. Si no existe `datos/peru_departamental_simple.geojson`, usa primero la skill `descargando-enaho`.
3. Corre exactamente:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py --indicador <indicador> --anio <año>
   ```

   `<indicador>` es `pobre` (por defecto) o `pobre_extremo`, o el argumento recibido (`$0`). `<año>` es 2024 salvo que pidan otro.

4. Si el script falla en un `assert`, **detente**: la unión o la ponderación están mal. No dibujes el mapa por otro camino.
5. Responde con la ruta del PNG, los tres departamentos con más y menos pobreza que imprimió el script, y la nota «25 de 25 con dato».

## Reglas fijas (ya están en el script)

- Une por código: `ubigeo[:2]` con `FIRST_IDDP`. **Nunca por nombre**: «APURIMAC» no es «Apurímac».
- Exige 25 departamentos y ninguno sin dato.
- Lima (15) y Callao (07) van separados.
- Un solo tono de claro a oscuro (`Reds`), desde 0; nunca arcoíris.
- Leyenda con la unidad: «% de personas».
- Pondera como el INEI: sumaria con `factor07 × mieperho`.
- Referencias 2024 que el script comprueba (deben salir exactas a un decimal): Cajamarca 45.0 %, Loreto 43.0 %, Puno 39.9 %, Ica 6.0 %, Moquegua 11.0 %, Madre de Dios 11.1 %.
