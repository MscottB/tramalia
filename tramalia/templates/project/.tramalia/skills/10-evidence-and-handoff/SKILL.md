---
name: 10-evidence-and-handoff
description: Cerrar con evidencia y traspaso
---

# Evidence and handoff

## Propósito
Cerrar con evidencia y traspaso.

## Cuándo usar
al finalizar un bloque de trabajo o cambiar de agente.

## Workflow
1. Ejecutar `tramalia close` (gates → evidence pack → handoff enlazado).
2. Completar summary, risks, rollback y next-steps del pack.
3. Verificar la entrada en `tramalia log`.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Evidence pack completo + entrada de handoff en docs/ai/07.
