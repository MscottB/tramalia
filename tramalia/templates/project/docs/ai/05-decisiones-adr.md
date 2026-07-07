# 05 — Decisiones de arquitectura (ADR)

Regla: toda decisión que afecte a **más de un módulo** o sea **difícil de revertir**
(framework, esquema, contrato de API, infraestructura, proveedor) se registra aquí.
El agente **propone** el ADR; un humano lo aprueba antes de implementarse.

Formato (copiar por cada decisión, más reciente arriba):

---

## ADR-001 — [título corto de la decisión]
- **Fecha:** YYYY-MM-DD · **Estado:** propuesta | aceptada | reemplazada por ADR-XXX
- **Contexto:** qué problema o fuerza motiva decidir (2-4 líneas).
- **Decisión:** qué se decidió, en una frase afirmativa.
- **Alternativas descartadas:** cuáles y por qué (1 línea c/u) — evita re-litigar.
- **Consecuencias:** qué se gana, qué se paga, qué queda prohibido a partir de ahora.
- **Tarea:** TASK-XXX (el `close` de esa tarea es la evidencia de implementación).
