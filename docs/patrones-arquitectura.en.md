# Architecture patterns

Tramalia **doesn't impose** an architecture style — that's not its role (*"it doesn't implement capabilities, it orchestrates them"*, the same principle behind the whole product). What it does: it leaves an **explicit decision point** in `docs/ai/01-arquitectura.md`, so the team (or the agent, proposing, with human approval) **declares** which one it uses, instead of it staying implicit or — worse — over-built by default.

## Why this matters (and why it's NOT "always use DDD")

Before this change, the architecture template shipped a dependency rule — *"UI → application → domain"* — **for every project alike**, unnamed and with no alternatives offered. That's, without saying so, a flavor of Domain-Driven Design / Hexagonal — and applying it to a simple CRUD is exactly what Ponytail/YAGNI forbids: over-abstracting, building layers nobody needs yet.

## The 4 styles

### CRUD (Create · Read · Update · Delete)
- **What it is:** the app is a direct bridge between the user and the database — no domain layer in between.
- **When:** small systems, admin panels, blogs, little business-rule processing.
- **Cost if you're wrong:** if the business grows and rules get complex, migrating hurts — but for a simple project, bolting on DDD from day 1 costs *more* than that future migration (YAGNI).

### Transaction Script
- **What it is:** one function/file per user action ("create order", "cancel subscription"), step-by-step logic, without modeling the domain as objects.
- **When:** short, direct processes with little logic shared between actions.
- **Analogy:** a cooking recipe — follow steps 1 through 5 and you're done.

### Domain-Driven Design (DDD) — with Hexagonal/Onion as its protective architecture
- **What it is:** you model the code to reflect **how the business actually works**, with a **ubiquitous language** — the same vocabulary between whoever codes and whoever knows the business (if the expert says "booking", the code says `Booking`, not `Reservation_Record_2`). Hexagonal/Onion is the architecture that protects that domain: the core doesn't import infrastructure, infrastructure imports the core.
- **When:**
  - The business has **complex rules** (logistics, finance, insurance).
  - The system is expected to **grow and last for years**, not a prototype.
  - You work with **microservices** (DDD's *bounded contexts* map naturally to services).
- **Hexagonal/Onion without full DDD:** it's also valid to use just the protective architecture (isolating the core from the database/framework) without the full DDD apparatus (ubiquitous language, aggregates, *bounded contexts*) — they're **complementary, not a closed package**.

### Data-Oriented Design
- **What it is:** instead of modeling business objects/concepts, you organize data so it moves fast through hardware memory.
- **When:** video games, simulations, any system where execution speed trumps domain expressiveness.
- **Analogy:** arranging a train's cars so it moves as fast as possible.

## How you declare it in your project

In `docs/ai/01-arquitectura.md` (which `init` generates and `AGENTS.md` requires reading before touching code):

```markdown
## Estilo arquitectónico de este proyecto
- Estilo declarado: [CRUD · Transaction Script · Domain-Driven Design (+ Hexagonal) · Data-Oriented Design]
- Por qué: [1-2 lines of business/domain justification]
```

**Default if you declare nothing:** the simplest one that solves the task — never DDD/Hexagonal by default. The same file's "Dependency rules" section **only applies if you declared** Domain-Driven Design/Hexagonal/Onion.

## If the project changes style

Moving from CRUD to DDD because the business grew is a decision that affects more than one module and is hard to reverse — exactly what warrants an **ADR** in `docs/ai/05-decisiones-adr.md` (the agent proposes it, the human approves it). It's not a silent change.

## What Tramalia does NOT do here

It doesn't generate domain code, doesn't validate that your code follows the declared style (that's the human/AI reviewer's job, with `01-arquitectura.md` as the reference), and **doesn't infer the style from the detected stack** — Angular+.NET+Postgres doesn't tell you whether your business is complex logistics or a simple panel; that's a business decision, not a technical one, and Tramalia doesn't have that information. It's decision documentation, not a gate.
