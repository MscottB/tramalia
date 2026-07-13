---
name: 06-security-gate
description: Aplicar el gate de seguridad
---

# Security gate

## Propósito
Aplicar el gate de seguridad.

## Cuándo usar
si el cambio toca auth, datos, APIs o dependencias.

## Workflow
1. Aplicar docs/ai/04-reglas-seguridad.md (inputs, secretos, logs, authz).
2. Correr Semgrep/Gitleaks vía `tramalia close` (gate security).
3. Clasificar hallazgos: real · falso positivo · requiere análisis · aceptado con mitigación.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
`security-salida.txt` en el paquete formal, con hallazgos clasificados y hash en
`metadatos.json`.
