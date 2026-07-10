# 01 — Arquitectura

> Completa las secciones marcadas; los agentes leen este archivo ANTES de tocar código.

## Vista general
[Diagrama o descripción de 5-10 líneas: capas, módulos principales y cómo fluyen los datos.]

## Estilo arquitectónico de este proyecto
> Elígelo por el **dominio de negocio**, no por el stack — Tramalia no lo infiere ni lo impone. Detalle y criterio completo: [Patrones de arquitectura](https://mscottb.github.io/tramalia/patrones-arquitectura/).

- **Estilo declarado:** [CRUD · Transaction Script · Domain-Driven Design (+ Hexagonal/Onion) · Data-Oriented Design]
- **Por qué:** [1-2 líneas: qué del dominio/negocio lo justifica]

**Default si no se declara:** el más simple que resuelva la tarea (CRUD o Transaction Script) — Ponytail/YAGNI. No asumas DDD/Hexagonal por defecto; súbelo solo cuando el dominio lo pida.

## Reglas de dependencia (qué puede importar qué)
> Aplica **solo si el estilo declarado es Domain-Driven Design / Hexagonal / Onion**. Con CRUD o Transaction Script, esta sección no rige — no la fuerces.

- La dirección de dependencia va **del borde al centro**: UI → aplicación → dominio. El dominio no importa infraestructura.
- Un módulo nuevo declara aquí **a qué capa pertenece** antes de escribirse.
- Prohibido el import circular; si aparece, es señal de que falta extraer un módulo.

## Límites que NO se cruzan
- [ej.: la UI nunca consulta la base de datos directo; siempre vía servicio/API]
- [ej.: el código legacy en `X/` no se modifica sin tarea explícita — ver skill 11]

## Decisiones vigentes
Toda decisión que afecte a más de un módulo o sea **difícil de revertir** (framework, esquema de datos, contrato de API, infraestructura) se registra como ADR en `docs/ai/05-decisiones-adr.md` — el agente **propone** el ADR, el humano lo aprueba.

## Puntos de extensión
[Dónde se agregan features nuevas sin tocar el núcleo: rutas, handlers, plugins…]

## Deuda arquitectónica conocida
| Qué | Riesgo | Plan |
|---|---|---|
| [ej.: módulo pagos acoplado a proveedor] | medio | tarea TASK-XXX |
