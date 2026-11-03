# Evaluación: con y sin skills

Cada pedido se corrió con `claude -p` en una copia limpia del repositorio, con `datos/` ya descargado y **sin** `salidas/`, `figuras/` ni `mapas/` (para forzar el encadenamiento). Fecha: 3 de noviembre de 2026.

```bash
claude -p "<pedido>"                              # con skills
claude -p --disallowedTools Skill "<pedido>"      # sin skills (y sin la carpeta .claude/)
```

## Resultados

| Pedido | Skills que se activaron | Cifra con skills | Cifra sin skills | Referencia |
|---|---|---|---|---|
| ¿Cuál fue la pobreza en Cusco en 2024? | `limpiando-enaho` | 18.5 % | 18.5 % | 18.5 % |
| Grafica la pobreza urbana y rural | `graficando-enaho` → `limpiando-enaho` | 24.7 % / 39.4 % | 24.8 % / 39.3 % | 24.8 % / 39.3 % |
| Haz un mapa de la pobreza por departamento | `mapeando-enaho` → `limpiando-enaho` | Cajamarca 45.0 %, Ica 5.9 % | Cajamarca 45.0 %, Ica 6.0 % | Cajamarca 45.0 %, Ica 6.0 % |

Los dos últimos pedidos activaron **dos skills seguidas**: como no existía la base limpia, la skill de gráficos o de mapas llamó primero a `limpiando-enaho`.

En esta corrida las skills ponderaban con `facpob07` sobre la base de personas y por eso diferían 0.1 puntos de la referencia. **Ya está corregido:** ahora departamento y área se calculan con la sumaria y `factor07 × mieperho`, como el INEI, y salen exactos: urbana 24.8 %, rural 39.3 %, Cajamarca 45.0 %, Loreto 43.0 %, Puno 39.9 %, Ica 6.0 %, Moquegua 11.0 %, Madre de Dios 11.1 %. El mapa comprueba esas seis cifras con `assert`.

## Qué cambió al tener las skills

| Aspecto | Con skills | Sin skills |
|---|---|---|
| Validación | Corre `limpiar.py`, lee `validacion.txt` (27.58 %, 108,664 residentes, unión `m:1`) antes de responder | Solo compara la cifra nacional; no revisa residentes ni uniones |
| Base reutilizable | `salidas/personas_2024.parquet`, con sexo, edad y área | No crea base de personas: trabaja solo con la sumaria y no podría cortar por sexo o edad |
| Archivos | Rutas fijas: `figuras/pobre_area_2024.png`, `mapas/pobreza_departamento.png` | Nombres y carpetas distintos en cada corrida (`pobreza_area_2024.png`, `mapa_pobreza_departamental_2024.png` en la raíz) |
| Gráfico | Un solo color, barras ordenadas desde cero, valor escrito, fuente al pie | Dos colores (total y extrema) y agrega una barra «Nacional» que no se pidió |
| Mapa | Escala desde 0, leyenda «% de personas», 25 de 25 comprobados con `assert` | Escala que empieza en ~6 %, no en 0 (exagera los contrastes); une por código, pero sin `assert` |
| Reproducibilidad | El mismo script da el mismo resultado cada vez | Escribe un script nuevo cada vez (`mapa_pobreza.py`, `pobreza_area_2024.py`) |

## Lo que aprendimos

- **Sin skills, Claude acertó las cifras.** El modelo ya conoce la ENAHO: usó la sumaria con `factor07 × mieperho` y unió por código. El valor de las skills no está en «acertar una vez», sino en que la limpieza, los nombres de archivo y el diseño sean **siempre iguales** y estén validados.
- **Primera corrida sin skills, descartada.** Con `--disallowedTools Skill` pero dejando `.claude/` en la copia, Claude encontró los scripts en `.claude/skills/*/scripts/` y los ejecutó directamente. Para medir de verdad la diferencia hubo que quitar la carpeta `.claude/`.
- **Las descriptions funcionan.** Las tres skills se activaron solas ante pedidos en lenguaje natural, sin usar `/`.
