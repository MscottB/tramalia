# 04 — Reglas de seguridad (gate seguridad)

Verificación delegada: Semgrep (SAST) + Gitleaks (secretos) (`tramalia security`).

## Reglas obligatorias
- Validar entradas en backend aunque el frontend valide.
- No registrar secretos, tokens, contraseñas ni datos sensibles en logs.
- Autorización por caso de uso, no solo por pantalla.
- No introducir dependencias sin revisar necesidad y riesgo.
- No conectar MCP remotos sin allowlist.

## Clasificación de hallazgos SAST
Cada hallazgo se marca como: real · falso positivo · requiere análisis · aceptado con mitigación.
