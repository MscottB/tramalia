# 03 — Reglas de base de datos (gate DB)

Verificación delegada: SQLFluff + dry-run de migraciones (`tramalia db check`).

## Reglas obligatorias
- Toda feature que toque datos indica las tablas afectadas.
- Toda tabla nueva define PK, constraints mínimos y naming consistente.
- Toda relación define FK o justifica por qué no aplica.
- Toda migración tiene rollback o plan manual explícito.
- Todo índice se justifica por consulta, unicidad, FK o performance.
- Todo dato personal documenta finalidad, retención y exposición en logs.
- Backend y frontend se alinean con el modelo de datos (sin duplicidad semántica).

## Naming
- Tablas:
- Columnas:
- Índices:
- Constraints:
