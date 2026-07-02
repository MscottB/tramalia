# 02 — Reglas de código

## Principios (Ponytail / YAGNI)
- Código simple, legible y mantenible; solución mínima correcta.
- Nombres explícitos; funciones pequeñas.
- Comentarios solo cuando aportan contexto.

## Manejo de errores
- Validar entradas.
- No ocultar excepciones.
- Registrar errores sin datos sensibles.

## Testing
- Agregar o actualizar tests si cambia lógica.
- Documentar validación manual si no hay tests.

Verificación delegada: gates `lint`/`format`/`test` (los ejecuta `tramalia close`).
