# 10 — Contexto operativo

> Lo que un agente (o humano nuevo) necesita para CORRER el proyecto sin preguntar.

## Entornos
| Entorno | URL/host | Rama | Quién despliega |
|---|---|---|---|
| local | — | cualquiera | tú |
| [staging] | [completa] | [main] | [CI / manual] |
| [producción] | [completa] | [tag] | [proceso de 12-deploy-release.md] |

## Correr en local
```bash
# [comandos exactos: levantar dependencias, migrar, arrancar]
```

## Configuración y credenciales
- Variables por entorno en `.env` (existe `.env.example` versionado; el `.env`
  real **jamás** se commitea — Gitleaks lo verifica, no lo esperes).
- Credenciales de servicios: [dónde viven — vault/secret manager], nunca en el repo.
- El agente **no lee** `.env` ni certificados sin avisar (regla de AGENTS.md).

## Observabilidad
- Logs: [dónde se miran en cada entorno].
- Errores/alertas: [Sentry/AppInsights/etc. y quién las recibe].
- Health checks: [endpoint(s)].

## Datos
- Datos de prueba: sintéticos (nunca dumps de producción con PII real).
- [Cómo obtener un dataset de desarrollo.]
