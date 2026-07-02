---
name: 01-spec-governance
description: Gobernar specs antes de código
---

# Spec governance

## Propósito
Gobernar specs antes de código.

## Cuándo usar
cada vez que se pida una feature nueva o un cambio de alcance.

## Workflow
1. Verificar que exista una tarea con ID en `specs/tasks.md` (crearla si falta).
2. Completar alcance, fuera de alcance y gates aplicables.
3. Si el proyecto usa Spec Kit, alinear con `/speckit.specify` y `/speckit.plan`.
4. No implementar nada sin tarea clara.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Entrada creada/actualizada en specs/tasks.md con ID y gates aplicables.
