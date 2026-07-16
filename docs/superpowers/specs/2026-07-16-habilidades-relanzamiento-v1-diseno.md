# Diseno de habilidades gobernadas y relanzamiento 1.0 BETA

**Fecha:** 2026-07-16

**Estado:** Aprobado por la autorizacion operativa previa del titular

**Rama de trabajo:** `codex/beta-implementation`

**Amplia:** `2026-07-12-tramalia-beta-stabilization-design.md`

## 1. Objetivo

Completar la nueva generacion BETA de Tramalia con un sistema de habilidades
versionado, explicable y configurable por proyecto; elevar el contenido propio
con metodologias de desarrollo, resiliencia de API, seguridad OWASP y UX; y
relanzar el producto en el repositorio actual con una identidad documental y
comercial coherente.

Esta ampliacion no reemplaza los contratos fail-closed, evidencia formal,
operaciones compartidas ni separacion de superficies del diseno BETA original.
Los extiende y corrige decisiones posteriores sobre activos, licencia y version.

## 2. Estado de partida comprobado

- `origin/main` y PyPI publican `0.33.0` bajo Apache-2.0.
- El trabajo nuevo vive en el worktree `codex/beta-implementation`.
- El baseline del worktree es de 661 pruebas aprobadas y una omitida en Python
  3.14; la cifra no es un objetivo de producto.
- El inventario de habilidades propias y entradas externas se deriva del
  catalogo; las cantidades observadas no forman parte del contrato.
- La rama de implementacion ya fija referencias externas por SHA y publica el
  lock de forma atomica.
- La activacion actual depende de bloques TOML comentados y no aisla fisicamente
  habilidades desactivadas.
- Semgrep y Gitleaks no estan instalados todavia en el entorno local.
- MkDocs Material ya es la base visual bilingue y debe conservarse.

## 3. Decisiones vinculantes

### 3.1 Repositorio y version

- Se limpia y relanza el repositorio existente `MscottB/tramalia`; no se elimina
  ni se recrea.
- `v0.33.0` queda como ultima version historica Apache-2.0.
- El desarrollo del corte legal usa `1.0.0.dev0`.
- La primera publicacion de la nueva generacion usa `1.0.0b1` y el tag
  `v1.0.0b1`.
- Tags, releases y versiones historicas de PyPI no se borran.

### 3.2 Licencia y producto comercial

- El motor y la CLI futuros usan PolyForm Noncommercial 1.0.0, sujetos a una
  auditoria de titularidad satisfactoria.
- El uso comercial requiere un acuerdo separado; el archivo informativo del
  repositorio no concede por si solo esos derechos.
- Las plantillas y archivos destinados a proyectos generados conservan
  Apache-2.0 para que el proyecto del cliente no herede la restriccion del motor.
- La distribucion declara las licencias aplicables mediante PEP 639 y conserva
  todos los textos legales correspondientes.
- Marca, logotipo y presentacion oficial se regulan por una politica de marcas.
- Servicios alojados, conectores empresariales y componentes de operacion
  comercial pueden mantenerse privados y propietarios.
- El repositorio y la documentacion describen el codigo como `source-available`,
  no como open source.

### 3.3 Activos visuales y documentacion

- Los tres PNG de `assets/images/` son maestros y no se eliminan.
- Su mapeo canonico es:
  - banner espanol -> README espanol;
  - logo neutro -> README ingles;
  - icono -> portada y marca de MkDocs.
- Los maestros se renombran sin espacios ambiguos y los WebP optimizados siguen
  siendo los archivos de entrega.
- Un manifiesto versionado registra maestro, derivado, uso, dimensiones, hash y
  texto alternativo.
- MkDocs Material sigue siendo el sistema visual; no se incorpora Figma.
- Mkdocstrings genera la referencia API dentro del mismo tema.

## 4. Vocabulario de gobierno

- **Habilidad:** procedimiento versionado que explica como realizar un trabajo.
- **Herramienta:** programa que ejecuta una capacidad concreta.
- **Puerta de calidad:** validacion automatica que decide si el trabajo puede
  continuar o cerrarse.
- **Evidencia:** registro verificable de que se ejecuto una puerta y de su
  resultado.
- **Perfil:** conjunto declarativo de habilidades recomendado u obligatorio para
  un tipo de proyecto.
- **Resolucion:** calculo determinista que combina catalogo, perfil, tecnologia,
  herramientas y decisiones explicitas.
- **Excepcion:** autorizacion temporal, razonada y revisada para apartarse de una
  obligacion.

## 5. Arquitectura del sistema de habilidades

### 5.1 Catalogo tipado

Cada habilidad propia tiene una fuente canonica empacada e inmutable bajo
`tramalia/catalogo/habilidades_propias/<id>/`, con `SKILL.md` y
`habilidad.toml`. `.tramalia/habilidades/` es exclusivamente la proyeccion activa
de un proyecto y nunca se usa para cargar el catalogo canonico. El metadata
incluye:

- `version_esquema`, `id`, `nombre`, `version` y `categoria`;
- aplicabilidad por tecnologia, capacidad y tipo de proyecto;
- dependencias y conflictos;
- herramientas requeridas y opcionales;
- permisos y nivel de riesgo;
- activacion predeterminada independiente de la obligatoriedad;
- obligatoriedad predeterminada: obligatoria, recomendada u opcional;
- puertas, evidencia esperada y politica de excepcion tipada;
- fuentes con URL, version y fecha de revision.

El catalogo externo deja de depender de bloques comentados. Las sugerencias
curadas viven en un archivo estructurado de solo lectura distribuido por
Tramalia. El manifiesto del proyecto conserva exclusivamente su intencion y sus
fuentes personalizadas.

### 5.2 Intencion del proyecto

`.tramalia/habilidades.toml` usa `version_esquema = 1`, una lista explicita de
perfiles, selecciones con estado `activa` o `inactiva` y fuentes personalizadas
tipadas. Una seleccion puede incluir motivo y una excepcion estructurada. Una
fuente personalizada declara ID canonico, URL HTTPS, referencia y licencia; su
presencia no autoriza descarga ni activacion.

`.tramalia/habilidades.lock.json` usa tambien `version_esquema = 1`. Cada entrada
conserva fuente canonica, referencia, SHA completo, hash de contenido canonico y
licencia. Configuracion y lock heredados se migran de forma fail-closed,
idempotente y con round-trip probado; una entrada ambigua o incompleta bloquea la
migracion sin reescribir el original.

Los comentarios son documentacion, nunca estado de la aplicacion. TOML invalido
produce un error tipado y no un catalogo vacio.

### 5.3 Resolucion reproducible

El resolvedor recibe:

1. catalogo vigente;
2. tecnologia y capacidades detectadas;
3. herramientas presentes;
4. perfiles declarados;
5. selecciones explicitas;
6. lock instalado;
7. instante UTC consciente, proporcionado por un reloj inyectable.

La precedencia de activacion es:

1. seleccion explicita valida;
2. obligacion del perfil;
3. recomendacion del perfil;
4. sugerencia por deteccion;
5. valor predeterminado del catalogo.

La obligatoriedad efectiva se resuelve por separado y conserva el valor mas
fuerte entre perfiles aplicables: `obligatoria`, `recomendada`, `opcional`. Una
seleccion explicita inactiva sobre una obligacion solo es valida con excepcion
completa, vigente y permitida por la politica de la habilidad. Una seleccion
explicita activa nunca supera incompatibilidad, conflicto, dependencia inactiva
ni herramienta requerida ausente: esas condiciones bloquean la aplicacion. Las
habilidades no aplicables por tecnologia, capacidad o tipo de proyecto permanecen
inactivas con razon estable y no requieren excepcion. Empates, multiples perfiles
y dependencias se ordenan por ID canonico.

El resultado es un plan inmutable con decisiones, razones, dependencias,
conflictos, herramientas faltantes, configuracion objetivo, diff de
materializacion y huellas de todos los insumos: catalogo, perfiles,
configuracion, lock, cache verificada, deteccion y herramientas. Planificar y
explicar no escriben ni acceden a la red. Al aplicar se revalidan esos insumos y
la vigencia temporal dentro de un lock interproceso.

### 5.4 Estados ortogonales

Una sola etiqueta no puede expresar correctamente que una habilidad sea, por
ejemplo, obligatoria, activa, instalada, modificada y con actualizacion
disponible al mismo tiempo. El modelo conserva dimensiones independientes:

- **activacion:** `activa` o `inactiva`;
- **obligatoriedad:** `obligatoria`, `recomendada` u `opcional`;
- **compatibilidad:** `compatible`, `pendiente_herramienta`, `incompatible` o
  `bloqueada_conflicto`;
- **instalacion:** `instalada` o `no_instalada`;
- **integridad:** `no_verificada`, `verificada`, `modificada` o `invalida`;
- **actualizacion:** `no_consultada`, `actual`, `disponible` o
  `error_consulta`.

Un estado compuesto agrega metadata, decision, observacion y procedencia sin
colapsarlas. La TUI y la salida JSON conservan cada dimension; nunca las reducen
a un booleano ambiguo ni mezclan politica, filesystem y red en un unico estado.

### 5.5 Activacion efectiva

Solo las habilidades activas se materializan en la ruta que `AGENTS.md` ordena
leer. El catalogo y la cache no forman parte de esa ruta activa.

- Una habilidad propia activa se materializa desde su fuente canonica empacada.
- Una externa activa se restaura exactamente desde el SHA bloqueado.
- Desactivar retira la proyeccion activa mediante una transaccion serializada y
  recuperable sin borrar la cache ni el lock.
- Una copia modificada por el usuario nunca se elimina silenciosamente; la
  operacion se bloquea y explica como conservar o migrar el cambio.
- No se usan enlaces simbolicos, para conservar comportamiento equivalente en
  Windows, Linux y macOS.

La operacion compuesta no se describe como atomicidad global: reemplazar un
arbol, configuracion y lock requiere varios renames. Un lock interproceso,
journal de fases, staging en el mismo volumen, revalidacion TOCTOU, backups y
recuperacion al abrir el proyecto garantizan que un fallo o reinicio converge al
estado anterior o al nuevo estado completo. El hash canonico usa rutas POSIX
ordenadas, bytes sin conversion de fin de linea, reglas explicitas para modos y
rechazo de colisiones Unicode/case-insensitive, nombres reservados, symlinks,
junctions y reparse points.

### 5.6 Perfiles iniciales

- `base`
- `api`
- `frontend`
- `datos`
- `legado`
- `release`
- `agentico`
- `mcp`
- `alta-seguridad`

Los perfiles iniciales y su contenido minimo son:

- `base`: obliga gobierno de especificacion, revision de calidad, ejecucion
  segura y evidencia/traspaso; recomienda minimalismo, ahorro de contexto,
  observabilidad y documentacion;
- `api`: obliga seguridad de aplicacion y recomienda resiliencia API;
- `frontend`: recomienda experiencia y accesibilidad;
- `datos`: obliga ingenieria de bases de datos y recomienda gobierno analitico;
- `legado`: obliga modernizacion de legado y recomienda observabilidad;
- `release`: obliga despliegue/lanzamiento y evidencia/traspaso;
- `agentico`: obliga seguridad de habilidades/MCP y recomienda modelado de
  amenazas y revision multiagente;
- `mcp`: obliga seguridad de habilidades/MCP y recomienda modelado de amenazas;
- `alta-seguridad`: obliga seguridad de aplicacion, modelado de amenazas y
  seguridad de habilidades/MCP cuando cada una aplica.

El archivo estructurado referencia IDs del catalogo y se valida por contenido e
ID, nunca mediante `len(...)`. Un perfil declara requisitos y recomendaciones,
pero no descarga herramientas ni habilidades. La IA puede sugerir un plan; nunca
lo aplica silenciosamente.

## 6. Habilidades propias

Los directorios y nombres propios se migran a espanol ASCII. El catalogo deja de
fijar una cantidad como contrato. La primera version contiene todo el inventario
historico mejorado y agrega:

- `17-resiliencia-api`;
- `18-seguridad-habilidades-mcp`;
- `19-experiencia-accesibilidad`.

Todas las habilidades siguen un contrato editorial comun:

1. objetivo;
2. cuando aplica y cuando no;
3. precondiciones;
4. procedimiento;
5. puertas de calidad;
6. evidencia esperada;
7. excepciones;
8. fuentes versionadas.

### 6.1 Metodologia de desarrollo

El conjunto base cubre especificacion, criterios de aceptacion, ADR, TDD, cortes
verticales, revision basada en riesgo, migracion y rollback, observabilidad,
release y traspaso. No exige una cantidad fija de pruebas.

### 6.2 Resiliencia de API

La habilidad cubre timeouts, concurrencia acotada, idempotencia, respeto de
`Retry-After`, backoff exponencial con jitter, presupuestos de reintentos,
deduplicacion, cache, circuit breaker, limites de recursos, telemetria y pruebas
deterministas de 429, 503, timeout y recuperacion.

### 6.3 Seguridad

La seguridad usa una matriz de aplicabilidad, no una afirmacion universal de
cumplimiento. Las referencias iniciales son:

- OWASP Top 10 2025;
- OWASP API Security Top 10 2023;
- OWASP ASVS 5.0.0;
- OWASP Agentic Skills Top 10, marcado con su nivel de madurez;
- OWASP MCP Top 10, marcado con su nivel de madurez.

Semgrep y Gitleaks son controles parciales dentro de puertas reproducibles; no
constituyen certificacion. La habilidad agentica cubre procedencia, permisos,
instrucciones no confiables, prompt/command injection, tool poisoning, secretos,
aislamiento, drift, inventario, auditoria MCP y sobreexposicion de contexto.

### 6.4 UX y accesibilidad

La habilidad de experiencia cubre jerarquia, estados, navegacion por teclado,
foco, contraste, movimiento reducido, anchos adaptables, contenido comprensible y
evidencia automatizada. Para web toma WCAG 2.2 AA como objetivo; para terminal
define equivalentes comprobables mediante Pilot y snapshots semanticos.

## 7. Superficies

### 7.1 CLI

Se incorporan comandos espanoles con aliases compatibles:

- `tramalia habilidades listar`;
- `tramalia habilidades planificar`;
- `tramalia habilidades explicar <id>`;
- `tramalia habilidades activar <id>`;
- `tramalia habilidades desactivar <id>`;
- `tramalia habilidades perfil aplicar <perfil>`;
- `tramalia habilidades auditar`.

`tramalia skills` permanece como alias durante la BETA. Texto y JSON se generan
desde los mismos modelos, sin recalcular politica.

### 7.2 TUI

La pantalla de habilidades muestra perfil, estado, razon, procedencia,
dependencias, conflictos, permisos, herramientas y SHA. Toda mutacion presenta
un plan/diff, solicita confirmacion y usa el coordinador global del Plan 03b
sobre el lock interproceso del nucleo.

La TUI permite activar y desactivar realmente, no solo instalar o actualizar.
Cancelacion, fallo y refresco posterior conservan los contratos de operaciones
observables.

### 7.3 MCP

MCP puede consultar catalogo, resolucion y auditoria. Las mutaciones requieren
una raiz gobernada, permisos declarados y consentimiento explicito de la
superficie anfitriona. Ninguna herramienta MCP descarga o activa por inferencia.

## 8. Pruebas y seguridad

- Toda conducta nueva sigue RED-GREEN-REFACTOR.
- Se prueban ciclos, dependencias faltantes, conflictos y precedencia.
- Se prueban TOML invalido, traversal, nombres reservados y enlaces simbolicos.
- Se prueban activacion/desactivacion transaccional, recuperacion tras fallos y
  preservacion de cambios locales.
- Se prueban locks, hashes, procedencia y fuentes no confiables.
- Se prueban perfiles sobre stacks Python/API, frontend, datos y MCP.
- Se prueban paridad CLI/TUI/JSON y ausencia de activacion silenciosa.
- La suite historica se consolida por contrato; no se conserva por alcanzar una
  cifra determinada.

## 9. Documentacion y activos

MkDocs incorpora:

- arquitectura de habilidades y flujo de resolucion;
- guia de perfiles;
- matriz de estados;
- explicacion de puerta, herramienta, habilidad y evidencia;
- metodologia de seguridad y limites de cumplimiento;
- referencia API generada;
- capturas reales de la TUI;
- paginas ES/EN de licencia y migracion 0.33 -> 1.0 BETA.

Los README son onboarding breve y no duplican conteos, versiones ni tablas que
puedan derivarse del catalogo.

## 10. Secuencia de implementacion

1. Integrar y verificar la base existente de `codex/beta-implementation`.
2. Ejecutar Plan 03a: seguridad y calidad UX web.
3. Ejecutar Plan 03c: catalogo, perfiles, resolucion, contenido y activacion.
4. Ejecutar Plan 03b: CLI/TUI interactiva sobre esos contratos.
5. Ejecutar Plan 04: licencia, activos, MkDocs y lanzamiento reproducible.
6. Validar Python 3.11-3.14, tres sistemas, paquete y documentacion.
7. Integrar en `main`, comprobar CI y crear `v1.0.0b1`.

## 11. Criterios de aceptacion

- Ninguna habilidad desactivada aparece en la ruta activa de agentes.
- Cada decision de resolucion tiene una razon estable y serializable.
- Un perfil produce el mismo plan con las mismas entradas.
- Una habilidad obligatoria no se desactiva sin excepcion valida.
- Las dependencias se ordenan y los ciclos bloquean la aplicacion.
- Fuentes externas activas tienen SHA completo, hash y licencia inventariada.
- CLI, TUI y JSON muestran los mismos estados.
- Semgrep, Gitleaks y auditoria de habilidades fallan de forma visible.
- Las referencias OWASP incluyen version y nivel de madurez.
- README ES, README EN y MkDocs usan el activo visual asignado.
- MkDocs Material y mkdocstrings compilan en ES/EN con modo estricto.
- Metadata, changelog, tag, wheel y sdist coinciden en `1.0.0b1`.
- GitHub Release usa los artefactos validados y PyPI no reconstruye.

## 12. Fuera de alcance de la primera BETA

- Marketplace remoto propio de Tramalia.
- Firma criptografica de terceros para habilidades.
- Servicio cloud multi-tenant.
- Precios o contratos comerciales generados automaticamente.
- Certificacion formal OWASP, ASVS o WCAG.
- Eliminacion o reescritura de la historia Apache existente.
