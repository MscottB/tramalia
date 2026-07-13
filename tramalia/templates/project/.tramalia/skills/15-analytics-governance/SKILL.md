---
name: 15-analytics-governance
description: Cerrar tareas de datos/ML con métricas y umbrales como evidencia
---

# Analytics governance

## Propósito
Que un cierre de datos/ML registre *con qué datos* y *qué números* — y que una
regresión de métrica bloquee el cierre en vez de pasar en silencio.

## Cuándo usar
Tareas que producen o modifican pipelines, notebooks, modelos o queries analíticas.

## Workflow
1. Aplicar `docs/ai/13-analitica-datos.md` (notebooks limpios y ejecutables,
   validaciones de datos como gate, dialecto SQL correcto).
2. Antes de cerrar, escribir `.tramalia/metrics.json`: dataset (nombre + hash),
   métricas del run y referencia externa (p. ej. `mlflow_run`).
3. Si la tarea tiene mínimos acordados, declararlos en `.tramalia/thresholds.json`
   (`{"accuracy": {"min": 0.90}}`) — un incumplimiento **bloquea** el close.
4. `tramalia close TASK-XXX`: las métricas se validan y normalizan en
   `metricas.json` y `metadatos.json`; el estado es `bloqueado` si falla un umbral.

## Guardrails
- Nunca inventar ni redondear métricas: se copian del output real del run.
- Bajar un umbral es decisión humana → ADR en `docs/ai/05`, no un edit silencioso.
- Datos reales con PII jamás en el evidence pack: identificadores y hashes, no filas.

## Evidencia esperada
`metricas.json` + `umbrales-metricas.txt` en el paquete;
`metadatos.json → metricas/umbrales` consultable desde `tramalia log`.
