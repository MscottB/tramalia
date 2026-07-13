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
5. Guardar el checklist y trigger de rollback en el runbook o ADR versionado,
   referenciarlo desde la tarea y ejecutar `tramalia close TASK-XXX`.

## Guardrails
- Sin rollback probado no hay deploy — se bloquea la tarea, no se "avisa".
- Cambios destructivos de BD requieren aprobación humana explícita.
- Si el trigger de rollback se dispara: rollback primero, análisis después.

## Evidencia esperada
Paquete formal del cierre con salidas, hashes, identidad Git, versión de Tramalia
y estado honesto. El traspaso conserva el ID de tarea; el checklist y rollback
permanecen en el runbook o ADR versionado enlazado desde `specs/tasks.md`.
`tramalia log` queda como historial de releases.
