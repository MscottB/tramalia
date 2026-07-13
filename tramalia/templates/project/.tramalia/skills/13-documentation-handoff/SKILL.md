---
name: 13-documentation-handoff
description: Documentar para el siguiente
---

# Documentation handoff

## Propósito
Documentar para el siguiente.

## Cuándo usar
al cerrar features o releases.

## Workflow
1. Actualizar docs/ai/00 (estado), 01 (arquitectura) y 05 (ADR) si cambió algo.
2. Dejar próximos pasos accionables en `specs/tasks.md`.
3. Ejecutar `tramalia handoff TASK-XXX`; su `traspaso.md` canónico debe permitir
   a otro agente continuar sin contexto verbal.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
`docs/ai` y `specs/tasks.md` actualizados + paquete formal de traspaso.
