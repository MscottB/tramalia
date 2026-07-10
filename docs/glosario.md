# Glosario

Definiciones cortas de los términos que aparecen en la documentación. Usa el buscador (arriba) para saltar a uno.

| Término | Qué significa |
|---|---|
| **ADR** (Architecture Decision Record) | Documento corto que registra una decisión técnica, su contexto y consecuencias. En Tramalia viven en `docs/ai/05`. |
| **AGENTS.md** | Archivo estándar (Linux Foundation) con las reglas del proyecto que **leen todos los agentes IA**. Fuente única de verdad. |
| **Agente IA** | Herramienta que lee contexto, razona, edita archivos y/o ejecuta comandos (Claude Code, Codex, Cursor, Antigravity…). |
| **Bootstrap** | Herramientas **base que instalas manualmente primero** (mise, git, uv), porque no pueden instalarse solas. Una vez presentes, `mise install` trae todo lo demás. |
| **Bundle** (Databricks Asset Bundle) | Definición declarativa de jobs/pipelines de Databricks (`databricks.yml`). El gate **`bundle`** lo valida (`databricks bundle validate`) antes de desplegar. Ver [Analítica](analitica.md). |
| **CLI** (Command-Line Interface) | Interfaz de línea de comandos: se usa escribiendo comandos en la terminal. |
| **Copyleft** | Tipo de licencia que obliga a mantener abierto el código derivado (GPL, LGPL, MPL). En Tramalia no afectan porque las tools se *invocan*, no se enlazan. |
| **CRUD** (Crear, Leer, Actualizar, Borrar) | Estilo arquitectónico donde la app es un puente directo usuario↔base de datos, sin capa de dominio. Para sistemas pequeños con poca lógica de negocio. Ver [Patrones de arquitectura](patrones-arquitectura.md). |
| **Data-Oriented Design** | Estilo arquitectónico que organiza los datos para que se muevan rápido por la memoria del hardware, en vez de modelar objetos de negocio. Típico de videojuegos/simulaciones. |
| **DDD** (Domain-Driven Design) | Estilo arquitectónico que modela el código para reflejar el negocio real, con **lenguaje ubicuo**. Para dominios complejos (finanzas, logística) o sistemas de vida larga. Ver [Patrones de arquitectura](patrones-arquitectura.md). |
| **Enforcement** | Que Tramalia **bloquee** el cierre de una tarea si un gate falla (salvo excepción documentada con `--allow-fail`). |
| **Evidence pack** | Carpeta fechada con la **prueba verificable** de un cierre: comandos, salidas crudas, riesgos, rollback, próximos pasos y `metadata.json`. |
| **Fachada** (façade) | Capa fina que pone **una sola interfaz** delante de un subsistema complejo. El CLI y `tramalia mcp` son fachadas. |
| **Fan-out** | Propagar una fuente única (`AGENTS.md`) a los formatos de varios agentes (Cursor, Copilot…), con rulesync. |
| **Gate** (quality gate) | **Validación obligatoria** antes de cerrar una tarea: build, test, lint, seguridad, base de datos, UX/UI. |
| **Guardia de inicialización** | `close`/`evidence`/`handoff` **se bloquean (exit 1)** en un repo sin `tramalia init` — no hay gobierno sin convención. |
| **Handoff** | **Traspaso estructurado** entre agentes/sesiones: tarea → archivos → comandos → resultado → riesgos → pendientes → siguiente paso. |
| **Hexagonal / Onion** | Arquitectura que aísla el núcleo del negocio de la infraestructura (BD, framework): el núcleo no importa infraestructura, ella lo importa a él. La "arquitectura protectora" con la que suele venir DDD — pero se puede usar sola. |
| **Horizonte** | Campo de `specs/tasks.md` (ahora · próximo · después) que planifica sin comprometer: re-planificar es **editar el archivo**; las tareas cerradas son inmutables por evidencia. |
| **i18n** (internacionalización) | Catálogos JSON (`tramalia/i18n/{es,en}.json`) que traducen la TUI y el CLI. Resolución: `TRAMALIA_LANG` > `config.json → language` > locale del sistema > inglés. |
| **Idempotente** | Que ejecutar dos veces produce el **mismo resultado** sin dañar nada. `tramalia init` es idempotente: no pisa lo existente. |
| **Ingesta** | Convertir conocimiento en formatos que el agente no lee bien (PDF, Word, Excel) a Markdown consumible. Lo hace **markitdown**. |
| **Interop** (interoperabilidad) | Herramientas externas **opcionales** que Tramalia orquesta pero **no requiere**; si faltan, sigue gobernando y lo registra como excepción. |
| **Lenguaje ubicuo** | En DDD, el **mismo vocabulario** entre quien programa y quien conoce el negocio — si el experto dice "reserva", el código dice `Reserva`, no `Booking_Record_2`. |
| **LSP** (Language Server Protocol) | Protocolo que da inteligencia de código (definiciones, referencias). Serena lo usa para navegar símbolos sin leer archivos enteros. |
| **MCP** (Model Context Protocol) | Protocolo estándar para conectar agentes IA con herramientas y datos. Tramalia expone una **fachada MCP** opcional. |
| **metadata.json** | Resumen estructurado de cada cierre (tarea, agente, timestamps, exit codes, estado) que hace la **auditoría consultable**. |
| **Moat** | El "foso" o **diferencial defendible** de un producto. En Tramalia: evidence pack, handoff, gates y auditoría repo-first. |
| **N0 / N1 / N2** (niveles de memoria) | N0 = archivos + CLI · N1 = fachada MCP · N2 = memoria persistente real (Engram / basic-memory / mem0). |
| **Ponytail / YAGNI** | Principios de **minimalismo**: haz lo mínimo correcto, no reconstruyas lo que ya existe, no abstraigas de más. |
| **Repo-first** | Usar **el repositorio como fuente de verdad**: todo lo importante queda versionado en él, no escondido en configs globales. |
| **SAST** (Static Application Security Testing) | Análisis **estático** de seguridad del código (lo hace Semgrep). |
| **Shell-out** | Que Tramalia **ejecute un comando externo** (subprocess) y muestre su salida tal cual, sin reimplementarlo. |
| **Snapshot** | Foto **empaquetada** del repo para consumo de IA (lo hace Repomix). |
| **Stack** | El conjunto de **tecnologías** de un proyecto (Angular, .NET, PostgreSQL…). `tramalia detect` lo identifica. |
| **Standalone** | Que **funciona por sí solo**, sin depender de nada externo. El núcleo de Tramalia es standalone (solo Python). |
| **Subagente** | Agente especializado que el modelo principal invoca para una tarea delegada, en contexto aislado y con **su propio `model:`** (ruteo por rol). Tramalia trae 5 en `.claude/agents/`. |
| **Token** | Unidad mínima de texto que consume un modelo IA. "Ahorrar tokens" = enviar menos contexto para reducir costo y latencia. |
| **Transaction Script** | Estilo arquitectónico: una función/archivo por cada acción del usuario, lógica paso a paso, sin modelar el dominio como objetos. Para procesos cortos y directos. |
| **TUI** (Text User Interface) | Interfaz interactiva **en la terminal** (Textual). `tramalia ui` la abre; solo lee e invoca el core, sin lógica propia. |
| **Wheel** | Formato de **paquete instalable** de Python (`.whl`); es lo que usa `pip install`. |

¿Falta algún término? Es un buen primer [aporte](https://github.com/MscottB/tramalia/blob/main/CONTRIBUTING.md).
