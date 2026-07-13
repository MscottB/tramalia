---
name: 05-code-quality-review
description: Revisar calidad de código
---

# Code quality review

## Propósito
Revisar calidad de código.

## Cuándo usar
antes de cerrar cualquier tarea que toque código.

## Workflow
1. Aplicar docs/ai/02-reglas-codigo.md (nombres, funciones, errores, tests).
2. Correr los gates lint/format/test — los ejecuta `tramalia close`.
3. No marcar terminado si un gate falla sin excepción documentada.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Gates de calidad en verde dentro del evidence pack.
