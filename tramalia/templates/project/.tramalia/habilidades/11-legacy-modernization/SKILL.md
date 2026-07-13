---
name: 11-legacy-modernization
description: Modernizar legado con red de seguridad
---

# Legacy modernization

## Propósito
Modernizar legado con red de seguridad.

## Cuándo usar
al tocar código antiguo o sin tests.

## Workflow
1. Inventariar con `tramalia context` + Serena antes de tocar.
2. Registrar cada intento fallido en docs/ai/06 para no repetirlo.
3. Cambios incrementales con gates en cada cierre; nunca big-bang.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Cierres pequeños auditados en `tramalia log`; intentos fallidos registrados.
