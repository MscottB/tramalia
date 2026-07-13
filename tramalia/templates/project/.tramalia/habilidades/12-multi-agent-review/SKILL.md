---
name: 12-multi-agent-review
description: Revisión cruzada entre agentes
---

# Multi agent review

## Propósito
Revisión cruzada entre agentes.

## Cuándo usar
en cambios de riesgo medio o alto.

## Workflow
1. Cerrar con `tramalia close --agent <ejecutor> --reviewer <revisor>`.
2. El revisor lee el paquete formal (salidas crudas + `metadatos.json`) antes de aprobar.
3. Registrar el resultado con `tramalia handoff`; el traspaso canónico queda en
   un paquete nuevo e inmutable.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Handoff con ejecutor y revisor; revisión basada en la evidencia del pack.
