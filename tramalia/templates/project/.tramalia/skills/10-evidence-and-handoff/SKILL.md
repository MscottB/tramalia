---
name: 10-evidence-and-handoff
description: Cerrar con evidencia y traspaso
---

# Evidencia y traspaso

## Propósito
Cerrar con evidencia y traspaso.

## Cuándo usar
al finalizar un bloque de trabajo o cambiar de agente.

## Workflow
1. Ejecutar `tramalia close` (puertas → paquete formal → traspaso enlazado).
2. Registrar riesgos y próximos pasos accionables en `specs/tasks.md`; si hay
   despliegue, documentar el rollback en un runbook o ADR versionado.
3. Verificar la entrada en `tramalia log`.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Paquete formal en `.tramalia/evidencia/` con `metadatos.json`, `traspaso.md` y
salidas de puertas; proyección visible en `docs/ai/07-traspaso-agentes.md`.
