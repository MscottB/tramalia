---
name: 08-tool-execution-gate
description: Cerrar solo con validación ejecutada
---

# Tool execution gate

## Propósito
Cerrar solo con validación ejecutada.

## Cuándo usar
al terminar cualquier tarea.

## Workflow
1. Ejecutar `tramalia close --task <ID>` — corre los gates y bloquea si fallan.
2. Nunca declarar 'funciona' sin salida cruda de los gates.
3. Usar --allow-fail solo con excepción anotada en risks.md.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Evidence pack con salidas crudas + metadata.json con status honesto.
