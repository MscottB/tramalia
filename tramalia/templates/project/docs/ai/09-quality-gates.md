# 09 — Quality gates

Los gates viven en `mise.toml` (los generó `init` para tu stack) y los ejecuta
`tramalia close` capturando su **salida cruda** en el evidence pack.

| Gate | Verifica | Cuándo aplica |
|---|---|---|
| build | compila | siempre que exista build |
| test | la lógica | siempre |
| lint / format | estilo y higiene (incl. notebooks limpios) | siempre |
| security | SAST + secretos (Semgrep/Gitleaks) | siempre |
| database | SQL con el dialecto correcto (SQLFluff + `.sqlfluff`) | si hay SQL |
| bundle | `databricks bundle validate` | si hay Asset Bundles |
| notebooks | ejecución de punta a punta (opt-in `--with-notebook-exec`) | analítica |
| ux | rendimiento + a11y (Lighthouse/Playwright/axe) | si hay frontend |

## Política de excepciones (`--allow-fail`)
- Un gate rojo **bloquea el cierre**. `--allow-fail` no lo "aprueba": lo registra
  como `passed_with_exceptions` con la razón anotada en `risks.md` del pack.
- Excepción sin razón escrita = cierre inválido; el revisor debe rechazarlo.
- Dos cierres seguidos con la misma excepción → crear tarea para arreglar la causa.

## Métricas con umbral (analítica/ML)
Si el proyecto define `.tramalia/thresholds.json`, una métrica que incumple
**bloquea igual que un gate** (ver `13-analitica-datos.md`).

## Agregar o ajustar un gate
Edita `mise.toml` (`[tasks.<gate>]`); el nombre debe estar en el orden estándar
(build/test/lint/security/database/bundle/notebooks/ux) para que `close` lo capture.
