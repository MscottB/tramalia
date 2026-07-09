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
1. **Analizar primero**: qué pide la tarea, qué archivos/módulos/datos toca.
2. Verificar que exista una tarea con ID en `specs/tasks.md` (crearla si falta).
3. Escribir el **plan con subpuntos** en la tarea: los pasos concretos a ejecutar.
4. Completar alcance, fuera de alcance, gates aplicables y **riesgos considerados**.
5. Si el proyecto usa Spec Kit, alinear con `/speckit.specify` y `/speckit.plan`.
6. **No implementar nada sin análisis, plan y (en tareas no triviales) confirmación.**

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Entrada creada/actualizada en specs/tasks.md con ID y gates aplicables.
