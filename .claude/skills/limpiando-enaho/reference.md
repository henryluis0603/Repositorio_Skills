# Referencia ENAHO

## Columnas de `salidas/personas_<año>.parquet`

`salidas/hogares_<año>.parquet` tiene una fila por hogar con las columnas del módulo 34, `ubigeo`, `estrato`, `departamento`, `urbano`, `area`, `pobre`, `pobre_extremo` y `peso = factor07 × mieperho`.

| Columna | Origen | Significado |
|---|---|---|
| `conglome`, `vivienda`, `hogar`, `codperso` | 02 | Llaves (texto) |
| `ubigeo` | 02 | Distrito, 6 dígitos (texto) |
| `departamento` | construida | `ubigeo[:2]`; Lima 15 y Callao 07 separados |
| `dominio` | 02 | 1–3 Costa, 4–6 Sierra, 7 Selva, 8 Lima Metropolitana |
| `estrato` | 02 | 1–5 urbano, 6–8 rural |
| `urbano`, `area` | construida | `estrato <= 5`; "Urbana" / "Rural" |
| `p203` | 02 | Parentesco con el jefe (1 jefe, 2 cónyuge, 3 hijo…) |
| `p204`, `p205`, `p206` | 02 | Preguntas de residencia (ya filtradas) |
| `p207`, `sexo` | 02 | 1 Hombre, 2 Mujer |
| `p208a`, `edad` | 02 | Años cumplidos |
| `grupo_edad` | construida | 0-13, 14-17, 18-29, 30-44, 45-59, 60+ |
| `facpob07` | 02 | Factor de expansión de personas |
| `pobreza` | 34 | 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `pobre`, `pobre_extremo` | construida | `pobreza <= 2`; `pobreza == 1` |
| `mieperho` | 34 | Miembros del hogar |
| `factor07` | 34 | Factor de expansión del hogar |
| `gashog2d`, `inghog2d` | 34 | Gasto e ingreso anual del hogar (deflactados) |
| `linea`, `linpe` | 34 | Línea de pobreza y de pobreza extrema (mensual per cápita) |

## Dos formas de ponderar

- **Oficial INEI** (`hogares_<año>.parquet`): sumaria con `factor07 × mieperho`. Da 27.58 % en 2024 (publicado: 27.6 %). Se usa para la validación, el mapa y todo corte por departamento o área: replica las cifras publicadas.
- **Base de personas** (`personas_<año>.parquet`): `facpob07`. Da 27.53 % en 2024. Se usa solo para cortes que la sumaria no tiene: sexo, edad.

No mezcles: con `facpob07`, por departamento la cifra difiere hasta 0.5 puntos de la oficial (Puno 40.4 % vs 39.9 %; Ica 5.9 % vs 6.0 %).

## Cifras de referencia 2024

| Indicador | Valor |
|---|---|
| Pobreza nacional | 27.6 % |
| Pobreza extrema | 5.5 % |
| Urbana / Rural | 24.8 % / 39.3 % |
| Cusco | 18.5 % |
| Cajamarca / Loreto / Puno | 45.0 / 43.0 / 39.9 % |
| Ica / Moquegua / Madre de Dios | 6.0 / 11.0 / 11.1 % |

## Agregar otro módulo

1. Bájalo con `descargando-enaho --modulos NN`.
2. Léelo con las mismas reglas (`convert_categoricals=False`, llaves como texto, nombres en minúscula).
3. Si es de personas (p. ej. 05 empleo), únelo a la base por `conglome, vivienda, hogar, codperso` con `validate="1:1"` y `how="left"`; comprueba que la base no cambie de tamaño.
4. Busca la variable en `datos/<año>/diccionario<año>.pdf`.

## Trampas vistas en 2024

- `aÑo` llega con la eñe rota; el script la renombra a `anio`.
- 117,721 filas en el módulo 200, pero solo 108,664 residentes habituales.
- `p204`–`p208a` tienen valores perdidos para quienes no responden; quedan fuera al filtrar residentes.
