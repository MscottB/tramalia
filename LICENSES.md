# Licencias

> **No es asesoría legal.** Este análisis es orientativo; para decisiones definitivas, valida con un abogado.

Tramalia usa **Apache-2.0** © 2026 Michael Jim Scott Bravo (ver [`LICENSE`](LICENSE) y [`NOTICE`](NOTICE)).

## Alcance del inventario

Este archivo registra hechos técnicos y licencias identificadas; no determina por sí solo compatibilidad, obligaciones ni riesgo legal. La validación definitiva corresponde a la revisión legal prevista en Plan 04 o a asesoría profesional.

Tramalia invoca varias herramientas externas como procesos CLI o servidores MCP y no redistribuye aquí sus ejecutables. La documentación sí redistribuye una adaptación del parcial de búsqueda de Material for MkDocs 9.7.6; se conserva su aviso MIT en [`AVISOS_TERCEROS.md`](AVISOS_TERCEROS.md).

## Código de terceros redistribuido

| Componente | Archivo adaptado | Licencia | Aviso |
|---|---|---|---|
| Material for MkDocs 9.7.6 | `docs/overrides/partials/search.html` | MIT | [`AVISOS_TERCEROS.md`](AVISOS_TERCEROS.md) |

Las dependencias Python importadas conocidas incluyen:

| Dependencia | Licencia |
|---|---|
| rich | MIT |
| questionary | MIT |
| mcp (SDK) | MIT |
| pytest (dev) | MIT |

La tabla es un inventario orientativo y debe actualizarse cuando cambien las dependencias o su forma de distribución.

## Herramientas externas del ecosistema

| Herramienta | Licencia identificada | Forma de uso actual |
|---|---|---|
| Semgrep (CE) | LGPL-2.1 | Proceso separado |
| pa11y | LGPL-3.0 | Proceso separado |
| axe-core | MPL-2.0 | Herramienta de pruebas instalada como dependencia de desarrollo |
| git | GPL-2.0 | Proceso separado |

Si cambia la forma de uso —por ejemplo, si se empaquetan binarios o se copian fuentes— se debe revisar el inventario y las condiciones aplicables antes de publicar.

## Por qué Apache-2.0 (y no otra)

- **Apache-2.0:** fue elegida para el código propio de Tramalia; su texto incluye una concesión expresa de patentes.
- **MIT, copyleft y licencias source-available:** siguen siendo alternativas con condiciones diferentes que requieren revisión según el modo concreto de uso y distribución.
