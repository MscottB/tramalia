# 09 - Puertas de calidad

Una puerta de calidad (quality gate) es un control automatizado que comprueba una
condición concreta antes de permitir el cierre de una tarea. Las puertas viven en
`mise.toml` (las generó `init` para tu stack) y `tramalia close` conserva la salida
cruda de cada una en el paquete de evidencia.

La política es **fail-closed**: una puerta roja bloquea y también se bloquea cuando
la configuración es inválida, falta el ejecutor o la comprobación no puede
terminar. No poder validar nunca se interpreta como aprobación.

| Puerta | Verifica | Cuándo aplica |
|---|---|---|
| build | compila | siempre que exista build |
| test | la lógica | siempre |
| lint / format | estilo y higiene (incl. notebooks limpios) | siempre |
| security | SAST + secretos (Semgrep/Gitleaks) | siempre |
| database | SQL con el dialecto correcto (SQLFluff + `.sqlfluff`) | si hay SQL |
| bundle | `databricks bundle validate` | si hay Asset Bundles |
| notebooks | ejecución de punta a punta (opt-in `--with-notebook-exec`) | analítica |
| ux | rendimiento + a11y (Lighthouse/Playwright/axe) | si hay frontend |

## Política de excepciones
- Una excepción revisada no aprueba una puerta roja: conserva el fallo y documenta
  por qué se acepta temporalmente el riesgo.
- Debe identificar razón, riesgo aceptado, control afectado, referencia, revisor y
  una expiración o condición de remediación. Si falta cualquiera, el cierre sigue
  bloqueado.
- `--allow-fail` por sí solo no basta para crear una excepción válida.
- Dos cierres seguidos con la misma excepción → crear tarea para arreglar la causa.

## Métricas con umbral (analítica/ML)
Si el proyecto define `.tramalia/thresholds.json`, una métrica que incumple
**bloquea igual que una puerta** (ver `13-analitica-datos.md`).

## Agregar o ajustar una puerta
Edita `mise.toml` (`[tasks.<puerta>]`); el nombre debe estar en el orden estándar
(build/test/lint/format/security/database/bundle/notebooks/ux) para que `close` lo
capture. Cada puerta conserva un archivo distinto `<puerta>-salida.txt`.
