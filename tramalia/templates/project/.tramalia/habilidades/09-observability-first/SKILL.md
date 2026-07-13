---
name: 09-observability-first
description: Diseñar con observabilidad
---

# Observability first

## Propósito
Diseñar con observabilidad.

## Cuándo usar
al crear servicios, endpoints o jobs.

## Workflow
1. Documentar logs/métricas/traces/health checks en docs/ai/01 (sección Observabilidad).
2. Registrar errores sin datos sensibles (docs/ai/04).
3. Definir cómo se detectará un fallo en producción antes de cerrar.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Sección de observabilidad actualizada en docs/ai/01.
