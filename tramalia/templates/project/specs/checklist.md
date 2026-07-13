# Checklist

## Antes de implementar
- [ ] Existe tarea clara en `specs/tasks.md` (con ID).
- [ ] Alcance y fuera de alcance definidos.
- [ ] Revisado docs/ai/03 si toca BD; 04 si toca seguridad; 11 si toca UI.
- [ ] Revisado docs/ai/06-intentos-fallidos.md.

## Después de implementar
- [ ] `tramalia close --task <ID>` ejecutado (puertas + paquete formal + traspaso).
- [ ] Estado honesto revisado en `tramalia log`.
- [ ] Riesgos y próximos pasos registrados en `specs/tasks.md`.
- [ ] Rollback documentado en un runbook o ADR versionado cuando corresponda.
- [ ] `metadatos.json`, `traspaso.md` y salidas revisados en el paquete formal.
