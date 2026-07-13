---
name: 16-threat-modeling
description: Análisis de amenazas ligero (STRIDE) antes de cambios sensibles
---

# Threat modeling

## Propósito
Ir más allá del SAST: pensar el ataque **antes** de escribir el código, no solo
escanear el código después.

## Cuándo usar
Cambios que tocan auth, permisos, PII, pagos, uploads, integraciones externas o
cualquier superficie expuesta nueva (endpoint, webhook, cola).

## Workflow
1. Describir el cambio en una frase: qué entra, qué sale, quién lo puede llamar.
2. Recorrer STRIDE sobre esa superficie (1-2 líneas por letra; "n/a" es respuesta válida):
   - **S**poofing: ¿puedo hacerme pasar por otro? · **T**ampering: ¿alterar datos en tránsito/reposo?
   - **R**epudiation: ¿negar que lo hice? (¿hay log?) · **I**nfo disclosure: ¿ver lo que no debo?
   - **D**oS: ¿tumbarlo con volumen/payloads? · **E**levation: ¿ganar permisos que no tengo?
3. Por cada amenaza real: mitigación concreta aplicando `docs/ai/04-reglas-seguridad.md`,
   o tarea nueva si excede el alcance.
4. Versionar la tabla STRIDE en `docs/ai/05-decisiones-adr.md` o un documento de
   amenaza referenciado por la tarea y cerrar con `tramalia close`; la puerta
   `security` (Semgrep/Gitleaks) valida lo escaneable.

## Guardrails
- Amenaza sin mitigación ni tarea = cierre bloqueado por el revisor.
- Cambios en auth/cripto/PII piden además revisión humana (regla de `04`).
- No documentar vectores explotables con detalle público innecesario.

## Evidencia esperada
Tabla STRIDE versionada y referenciada + `security-salida.txt` dentro del paquete.
