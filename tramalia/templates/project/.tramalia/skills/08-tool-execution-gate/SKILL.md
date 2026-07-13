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
3. Usar `--allow-fail` sólo con razón, riesgo, control, referencia, revisor y
   expiración o condición de remediación explícitos.

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Paquete en `.tramalia/evidencia/` con salidas `*-salida.txt`, hashes y
`metadatos.json` con `estado_cierre` honesto.
