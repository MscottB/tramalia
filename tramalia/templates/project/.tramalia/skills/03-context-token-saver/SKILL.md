---
name: 03-context-token-saver
description: Ahorrar tokens usando contexto derivado
---

# Context token saver

## Propósito
Ahorrar tokens usando contexto derivado.

## Cuándo usar
antes de leer código extenso o repos grandes.

## Workflow
1. Ejecutar `tramalia context` para refrescar tech-stack y project-map.
2. Usar Serena (MCP) para leer solo el símbolo a tocar; Repomix para snapshot.
3. Si Headroom está habilitado, usarlo para comprimir outputs largos (nunca la evidencia).

## Guardrails
- No ejecutar comandos destructivos sin confirmación.
- No leer ni exponer secretos.
- No modificar archivos fuera del alcance de la tarea.

## Evidencia esperada
Contexto derivado actualizado en .tramalia/context/.
