---
name: graficando-enaho
description: Grafica la pobreza monetaria o extrema de la ENAHO del INEI por área urbana/rural, sexo, grupo de edad o departamento, con barras ponderadas y reglas fijas de diseño, y guarda un PNG en figuras/. Úsala cuando pidan un gráfico, figura o comparación visual de la pobreza en el Perú con la ENAHO.
argument-hint: "[area|sexo|grupo_edad|departamento]"
allowed-tools: Bash(uv run *)
---

# Graficar la ENAHO

1. Si no existe `salidas/personas_2024.parquet` (o el del año pedido), usa primero la skill `limpiando-enaho`.
2. Elige `--por` según el pedido: `area`, `sexo`, `grupo_edad` o `departamento`. Elige `--indicador`: `pobre` (por defecto) o `pobre_extremo`. Corre exactamente:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por <grupo> --indicador <indicador> --anio <año>
   ```

   Para un subgrupo usa `--filtro`, por ejemplo `--filtro "area == 'Rural'"`.
3. Responde con las cifras que imprimió el script y la ruta del PNG. No recalcules a mano.
4. Si el pedido necesita un gráfico que el script no hace, escríbelo tú respetando todas las reglas de abajo.

## Reglas fijas (ya están en el script)

- Pondera siempre con `facpob07`: el eje es **% de personas**.
- Barras horizontales que empiezan en cero, ordenadas de mayor a menor (la edad va en su orden natural).
- Un solo color (`#1f4e79`); nada de colores por categoría.
- El valor escrito en cada barra, con un decimal.
- El título dice qué y cuándo: «Pobreza monetaria por sexo, Perú 2024».
- Nota al pie: «Fuente: INEI, ENAHO 2024».
- PNG a 200 dpi en `figuras/`.
