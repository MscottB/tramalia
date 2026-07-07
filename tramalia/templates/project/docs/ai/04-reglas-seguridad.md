# 04 — Reglas de seguridad (gate seguridad)

Verificación delegada: **Semgrep** (SAST) + **Gitleaks** (secretos), vía gate `security`.
El análisis de amenazas del cambio: skill `16-threat-modeling`.

## Checklist obligatorio (OWASP práctico)
- **Inyección**: toda query parametrizada; nada de concatenar SQL/comandos con input.
- **AuthN/AuthZ**: autorización por **caso de uso** (endpoint/acción), no solo por
  pantalla; deny-by-default; verificar propiedad del recurso (no solo el rol).
- **Entradas**: validar en backend aunque el frontend valide; listas blancas sobre
  listas negras; límites de tamaño en uploads y payloads.
- **Secretos**: nunca en el repo, ni en logs, ni en mensajes de error; viven en
  variables de entorno/vault por entorno. Gitleaks lo verifica — pero no lo esperes.
- **Sesiones/tokens**: expiración corta + refresh; invalidar al cambiar contraseña.
- **Errores**: mensajes genéricos al usuario, detalle al log (sin datos sensibles).

## Cadena de suministro (supply chain)
- Dependencia nueva: revisar mantenimiento (último release, issues), licencia y
  alternativas stdlib antes de agregarla.
- Lockfile siempre commiteado; actualizaciones de dependencias en tarea propia,
  no mezcladas con features.
- Ejecutar el audit del ecosistema en el gate `security` cuando exista
  (`npm audit`, `pip-audit`, `dotnet list package --vulnerable`).

## Clasificación de hallazgos SAST
Cada hallazgo se marca en el evidence pack como:
**real** (se corrige antes del close) · **falso positivo** (se anota por qué) ·
**requiere análisis** (tarea nueva) · **aceptado con mitigación** (documentada en risks.md).

## Cuándo escalar a humano
Cambios en auth, criptografía, manejo de PII o permisos **siempre** piden revisión
humana además del gate — el agente lo deja explícito en el handoff.
