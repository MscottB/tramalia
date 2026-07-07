---
name: 14-deploy-gate
description: Gobernar un deploy/release como tarea con checklist y evidencia
---

# Deploy gate

## Propósito
Que ningún deploy salga sin checklist completo, rollback definido y evidencia auditable.

## Cuándo usar
Toda vez que la tarea sea un release/deploy (o incluya migraciones hacia un entorno real).

## Workflow
1. Crear/usar la tarea del release en `specs/tasks.md` (TASK-XXX).
2. Recorrer el checklist pre-deploy de `docs/ai/12-deploy-release.md` **antes** de tocar
   el entorno; escribir el trigger de rollback elegido.
3. Respetar el orden: BD (expansión) → backend → frontend; contracción en el siguiente release.
4. Ejecutar el deploy; monitorear la ventana definida.
5. `tramalia close TASK-XXX` — pegar el checklist completado (con lo marcado) en
   `summary.md` del evidence pack y el trigger de rollback en `risks.md`.

## Guardrails
- Sin rollback probado no hay deploy — se bloquea la tarea, no se "avisa".
- Cambios destructivos de BD requieren aprobación humana explícita.
- Si el trigger de rollback se dispara: rollback primero, análisis después.

## Evidencia esperada
Evidence pack del close con checklist completado, versión etiquetada y estado honesto.
`tramalia log` queda como historial de releases.
