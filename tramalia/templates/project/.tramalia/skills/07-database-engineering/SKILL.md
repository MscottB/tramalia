---
name: 07-database-engineering
description: Aplicar el gate de base de datos
---

# Database engineering

## Propósito
Aplicar el gate de base de datos.

## Cuándo usar
si el cambio toca esquema, migraciones o queries.

## Workflow
1. Aplicar docs/ai/03-reglas-base-datos.md (PK/FK, índices, rollback, retención).
2. Correr SQLFluff vía `tramalia close` (gate database).
3. Toda migración con rollback o plan manual explícito.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
`database-salida.txt` en el paquete formal; migración y rollback documentados en
la tarea, runbook o ADR referenciado.
