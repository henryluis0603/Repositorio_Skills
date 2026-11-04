---
name: descargando-enaho
description: Descarga los microdatos de la ENAHO (Encuesta Nacional de Hogares) del portal del INEI en formato STATA, para cualquier año de 2015 a 2024 y cualquier módulo (34 sumaria, 02 miembros del hogar, 05 empleo, etc.), los descomprime en datos/<año>/ y baja el GeoJSON de departamentos del Perú. Úsala cuando pidan bajar, descargar u obtener la ENAHO o sus módulos, o cuando otra skill de la ENAHO diga que faltan archivos en datos/.
argument-hint: "[año] [módulos...]"
allowed-tools: Bash(uv run *)
---

# Descargar la ENAHO

1. Corre exactamente, desde la carpeta de trabajo actual (no cambies de carpeta):

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/descargar.py --anio <año>
   ```

   `<año>` es el argumento recibido (`$0`); si no hay, usa 2024.

   - Si el usuario pide otros módulos, agrégalos: `--modulos 34 02 05`. Por defecto baja 34 y 02, que es lo que necesita `limpiando-enaho`.
   - `--listar` muestra los años y su código del INEI.
2. Lee la salida. Debe terminar en `Listo.` y mostrar los `.dta` extraídos en `datos/<año>/`.
3. Si un módulo da error, repórtalo tal cual; no inventes otra URL. Si un zip está corrupto, bórralo y vuelve a correr.
4. Nunca subas `datos/` a git: ya está en `.gitignore`.

## Lo que hay que saber

- El portal identifica cada encuesta por un código, no por el año: 2024 = 966, 2023 = 906, 2022 = 784. La tabla completa está en el script y fue verificada contra el nombre de la sumaria dentro de cada zip.
- URL: `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/<código>-Modulo<NN>.zip`. El módulo va con dos dígitos (`02`, no `2`).
- El script es idempotente: si el zip ya existe, no lo baja de nuevo.
- Cada zip trae el diccionario en PDF (`diccionario<año>.pdf`); úsalo para buscar variables nuevas.
- Para un año que no esté en la tabla, dile al usuario que busque el código en <https://proyectos.inei.gob.pe/microdatos/> (Consulta por encuestas → ENAHO Metodología actualizada → Condiciones de vida y pobreza) y agrégalo a `CODIGOS` en el script.
