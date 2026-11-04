---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros del hogar) de la ENAHO del INEI y arma una base de personas residentes con pobreza, área, sexo, edad, departamento y factor de expansión, validada contra la pobreza oficial. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular la pobreza del Perú por región, departamento, área, sexo o edad.
argument-hint: "[año]"
allowed-tools: Bash(uv run *)
---

# Limpiar la ENAHO

1. Si faltan `datos/<año>/sumaria-<año>.dta` o `datos/<año>/enaho01-<año>-200.dta`, usa primero la skill `descargando-enaho`.
2. Corre exactamente, desde la carpeta de trabajo actual (no cambies de carpeta):

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio <año>
   ```

   `<año>` es el argumento recibido (`$0`); si no hay, usa 2024.

3. Lee `salidas/validacion.txt`. Si dice `Estado: FALLÓ` o la pobreza difiere del INEI en más de 0.1 puntos, **detente** y muéstrale al usuario qué chequeo falló. No respondas con una base que no valida.
4. Responde con la base que corresponda; toda cifra va ponderada:
   - **Pobreza por departamento, área o nacional** → `salidas/hogares_<año>.parquet`, con el peso oficial del INEI (`peso = factor07 × mieperho`). Así salen las cifras publicadas.
   - **Por sexo, edad o cualquier variable de personas** → `salidas/personas_<año>.parquet`, con `facpob07`.

   ```python
   (h.pobre * h.peso).sum() / h.peso.sum() * 100            # hogares
   (p.pobre * p.facpob07).sum() / p.facpob07.sum() * 100    # personas
   ```

5. Antes de usar una variable que no está en la base, lee [reference.md](reference.md).

## No se discute

Estas decisiones ya están en el script. No las cambies ni las rehagas a mano:

- Llaves (`conglome`, `vivienda`, `hogar`, `codperso`) y `ubigeo` siempre como texto: pierden los ceros si son número.
- Solo residentes habituales: `(p204==1 & p205==2) | (p204==2 & p206==1)`. En 2024 son 108,664.
- Unión personas → hogar con `validate="m:1"`.
- `pobre = pobreza <= 2`. `pobreza` es un código (1, 2, 3), nunca se promedia.
- Cifras ponderadas: nunca cuentes encuestas. Lo que es del hogar (departamento, área) se pondera como el INEI, con `factor07 × mieperho`.

## Lo que sí decides tú

Qué cruce mostrar, cómo explicarlo y qué advertir: por ejemplo, que un departamento con pocos encuestados tiene más error, o que la cifra es de pobreza monetaria y no multidimensional.
