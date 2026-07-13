# 13 — Analítica y datos

> Gobierno de notebooks, calidad de datos y métricas — donde "funciona" no basta:
> importa con qué datos y con qué números.

## Notebooks
- **Outputs siempre limpios** antes de commitear (puerta `lint`: `nbstripout --verify`) —
  outputs sucios rompen diffs, filtran datos a git y hacen imposible el review.
- Ejecutables **de punta a punta** en orden (Run All) — la puerta opcional `notebooks`
  (`init --with-notebook-exec`) lo verifica de verdad.
- Parámetros al inicio del notebook (una celda de config), credenciales **jamás**
  dentro (usa variables de entorno / secret scope).
- Lógica reutilizada 2+ veces se extrae a `src/` con tests; el notebook la importa.

## Calidad de datos
- Las validaciones (Great Expectations, dbt tests, pandera) se agregan como
  comandos en una puerta de calidad de `mise.toml` — su salida cruda queda
  separada dentro del paquete de evidencia.
- Todo dataset de entrada queda identificado: nombre + versión/hash (ver Métricas).

## Métricas y umbrales (enforcement — skill 15)
Antes de cerrar una tarea de datos/ML, el pipeline o el agente escribe
`.tramalia/metrics.json`:

```json
{ "dataset": { "name": "ventas_2026Q3", "hash": "sha256:…" },
  "metrics": { "accuracy": 0.91, "drift": 0.02 }, "mlflow_run": "…" }
```

`tramalia close` valida el JSON y conserva sus valores semánticos en
`metricas.json` y en `metadatos.json`. El archivo se normaliza como JSON formal;
no se promete una copia byte a byte del texto de entrada.
Con `.tramalia/thresholds.json` (`{"accuracy": {"min": 0.90}}`), una métrica que
incumple —o que **falta**— **bloquea el cierre** como una puerta fallida. El
diagnóstico legible queda en `umbrales-metricas.txt`.

- Umbral que baja de versión a versión = decisión humana registrada como ADR.
- La regresión de una métrica nunca se "acepta" en silencio: `--allow-fail` la deja
  como excepción formal, con control, referencia, revisor y vigencia, dentro de
  `metadatos.json`; el resultado pasa a `aprobado_con_excepciones` y queda visible
  en `tramalia log`.

## SQL analítico
El dialecto vive en `.sqlfluff` (lo generó `init`: databricks/tsql/postgres).
Queries de más de [50] líneas llevan comentario de propósito y dueño.
