# Patrones de arquitectura

Tramalia **no impone** un estilo de arquitectura — no es su rol (*"no implementa capacidades, las orquesta"*, el mismo principio de todo el producto). Lo que sí hace: deja un **punto de decisión explícito** en `docs/ai/01-arquitectura.md`, para que el equipo (o el agente, proponiendo, con aprobación humana) **declare** cuál usa, en vez de que quede implícito o —peor— sobreconstruido por defecto.

## Por qué esto importa (y por qué NO es "usa siempre DDD")

Antes de este cambio, la plantilla de arquitectura traía una regla de dependencia *"UI → aplicación → dominio"* **para todo proyecto por igual**, sin nombrarla ni ofrecer alternativas. Eso es, sin decirlo, un sabor de Domain-Driven Design / Hexagonal — y aplicarlo a un CRUD simple es exactamente lo que Ponytail/YAGNI prohíbe: abstraer de más, construir capas que nadie necesita todavía.

## No depende de si hay frontend

Los 4 estilos se eligen por **complejidad del dominio de negocio**, no por la forma del proyecto. Aplican igual a un proyecto full-stack (front + backend + BD), a un backend solo-API, o a un servicio API+BD sin frontend propio. La "UI" de la regla de dependencia no es necesariamente una interfaz gráfica — es cualquier **adaptador de entrada**: un controller REST, un handler GraphQL, un consumer de cola, un comando CLI. Un microservicio sin frontend puede justificar DDD/Hexagonal igual que una app con frontend, si su dominio es complejo; y un panel admin con frontend puede quedarse en CRUD si su lógica es simple.

## Los 4 estilos

### CRUD (Crear · Leer · Actualizar · Borrar)
- **Qué es:** la app es un puente directo entre el usuario y la base de datos — sin capa de dominio intermedia.
- **Cuándo:** sistemas pequeños, paneles admin, blogs, poco procesamiento de reglas de negocio.
- **Costo si te equivocas:** si el negocio crece y las reglas se complican, migrar es doloroso — pero para un proyecto simple, meter DDD desde el día 1 cuesta *más* que esa migración futura (YAGNI).

### Transaction Script
- **Qué es:** una función/archivo por cada acción del usuario ("crear pedido", "cancelar suscripción"), lógica paso a paso, sin modelar el dominio como objetos.
- **Cuándo:** procesos cortos y directos, con poca lógica compartida entre acciones.
- **Analogía:** una receta de cocina — sigues los pasos del 1 al 5 y terminas.

### Domain-Driven Design (DDD) — con Hexagonal/Onion como su arquitectura protectora
- **Qué es:** modelas el código para reflejar **cómo funciona el negocio de verdad**, con un **lenguaje ubicuo** — el mismo vocabulario entre quien programa y quien conoce el negocio (si el experto dice "reserva", el código dice `Reserva`, no `Booking_Record_2`). Hexagonal/Onion es la arquitectura que protege ese dominio: el núcleo no importa infraestructura, la infraestructura importa el núcleo.
- **Cuándo:**
  - El negocio tiene **reglas complejas** (logística, finanzas, seguros).
  - El sistema va a **crecer y durar años**, no es un prototipo.
  - Trabajas con **microservicios** (los *bounded contexts* de DDD mapean naturalmente a servicios).
- **Hexagonal/Onion sin DDD completo:** también es válido usar solo la arquitectura protectora (aislar el núcleo de la base de datos/framework) sin todo el aparato de DDD (lenguaje ubicuo, agregados, *bounded contexts*) — son **complementarias, no un paquete cerrado**.

### Data-Oriented Design
- **Qué es:** en vez de modelar objetos/conceptos de negocio, organizas los datos para que se muevan rápido por la memoria del hardware.
- **Cuándo:** videojuegos, simulaciones, cualquier sistema donde la velocidad de ejecución manda sobre la expresividad del dominio.
- **Analogía:** organizar los vagones de un tren para que avance lo más rápido posible.

## Cómo se declara en tu proyecto

En `docs/ai/01-arquitectura.md` (que `init` genera y `AGENTS.md` obliga a leer antes de tocar código):

```markdown
## Estilo arquitectónico de este proyecto
- Estilo declarado: [CRUD · Transaction Script · Domain-Driven Design (+ Hexagonal) · Data-Oriented Design]
- Por qué: [1-2 líneas del dominio/negocio que lo justifica]
```

**Default si no declaras nada:** el más simple que resuelva la tarea — nunca DDD/Hexagonal por defecto. La sección "Reglas de dependencia" del mismo archivo **solo aplica si declaraste** Domain-Driven Design/Hexagonal/Onion.

## Si el proyecto cambia de estilo

Pasar de CRUD a DDD porque el negocio creció es una decisión que afecta a más de un módulo y es difícil de revertir — exactamente lo que amerita un **ADR** en `docs/ai/05-decisiones-adr.md` (el agente lo propone, el humano lo aprueba). No es un cambio silencioso.

## Qué NO hace Tramalia aquí

No genera código de dominio, no valida que tu código siga el estilo declarado (eso es del revisor humano/IA, con `01-arquitectura.md` como referencia), y **no infiere el estilo por el stack detectado** — Angular+.NET+Postgres no te dice si tu negocio es logística compleja o un panel simple; esa es una decisión de negocio, no técnica, y Tramalia no tiene esa información. Es documentación de decisión, no un gate.
