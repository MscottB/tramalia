# 12 — Deploy y release

> El deploy es una tarea como cualquier otra: tiene ID, gates y `close` con evidencia.

## Pre-deploy (checklist — skill 14-deploy-gate)
- [ ] Gates verdes: la tarea del release cerró con `tramalia close` (status `passed`).
- [ ] Migraciones con **rollback probado** en un entorno no productivo.
- [ ] El **trigger de rollback está definido ANTES** de desplegar (qué métrica/error
      lo dispara y quién decide) — no se improvisa durante el incidente.
- [ ] Cambios riesgosos detrás de **feature flag** (activar ≠ desplegar).
- [ ] Versión etiquetada (semver) y CHANGELOG actualizado.
- [ ] Ventana acordada; quién monitorea los primeros [15] minutos.

## Orden de despliegue
1. **Base de datos** (solo expansión — ver `03`): la app vieja debe seguir funcionando.
2. **Backend** (compatible con el frontend viejo).
3. **Frontend**.
4. Contracción de BD: en el **siguiente** release, nunca en el mismo.

## Post-deploy
- Smoke test de los flujos críticos: [lista corta].
- Monitoreo activo [15] min: errores, latencia, [métrica de negocio clave].
- Si se dispara el trigger → rollback **sin debate**; el análisis viene después.

## Evidencia
El deploy se cierra con `tramalia close TASK-XXX` — el checklist completado va al
evidence pack (la skill 14 lo estructura). `tramalia log` es tu historial de releases.

## Rollback
- App: [comando/proceso exacto para volver a la versión anterior].
- Datos: las migraciones de expansión no requieren rollback de datos; las de
  contracción son las peligrosas — por eso van separadas y aprobadas por humano.
