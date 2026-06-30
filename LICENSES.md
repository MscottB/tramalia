# Licencias y donaciones

> **No es asesoría legal.** Este análisis es orientativo; para decisiones definitivas, valida con un abogado.

Tramalia usa **Apache-2.0** © 2026 Michael Jim Scott Bravo (ver [`LICENSE`](LICENSE) y [`NOTICE`](NOTICE)).

## El principio clave

Tramalia **invoca** las herramientas externas como **programas separados** (subprocess CLI o servidores MCP). No enlaza sus librerías ni redistribuye su código. Bajo derecho de autor, ejecutar un programa separado **no crea una obra derivada**, así que **sus licencias no imponen condiciones a Tramalia** — ni siquiera las copyleft.

Las únicas licencias que importan para la de Tramalia son las de sus **dependencias Python** (las que se instalan e importan):

| Dependencia | Licencia |
|---|---|
| rich | MIT |
| questionary | MIT |
| mcp (SDK) | MIT |
| pytest (dev) | MIT |

**Todas son MIT** → Tramalia es libre de usar cualquier licencia. Se eligió **Apache-2.0** (permisiva + concesión de patentes).

## Las copyleft del ecosistema (no afectan a Tramalia)

| Herramienta | Licencia | ¿Afecta a Tramalia? |
|---|---|---|
| Semgrep (CE) | LGPL-2.1 | No — proceso separado |
| pa11y | LGPL-3.0 | No — proceso separado |
| axe-core | MPL-2.0 | No — proceso separado |
| git | GPL-2.0 | No — proceso separado |

Solo importarían si Tramalia **empaquetara o enlazara** su código. No lo hace. Si en el futuro se redistribuyen binarios de terceros dentro de Tramalia, habría que revisar caso por caso.

## Donaciones

La licencia **no** determina si puedes recibir donaciones. **Cualquier** licencia open source (MIT, Apache-2.0, GPL, AGPL) lo permite vía GitHub Sponsors / Open Collective. Están habilitadas con [`.github/FUNDING.yml`](.github/FUNDING.yml).

## Por qué Apache-2.0 (y no otra)

- **Apache-2.0 / MIT (permisivas):** máxima adopción, ideal para una capa de gobierno que quiere difundirse. Apache-2.0 añade concesión explícita de patentes y cláusula de marca. **← elegida.**
- **AGPL-3.0 + comercial (dual):** copyleft fuerte + venta de excepción comercial = ingreso real, pero reduce la adopción. Decisión de negocio para más adelante.
- **Source-available (BSL/FSL):** permite restricciones comerciales pero no es open source OSI → menos confianza/adopción. Excesivo para el objetivo de donaciones.
