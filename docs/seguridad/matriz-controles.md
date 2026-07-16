# Matriz de controles de seguridad verificables

Esta matriz relaciona amenazas con controles propios, fuentes primarias y pruebas
repetibles. Es un registro de evidencia y limitaciones, no una auditoría externa, una
certificación ni un aval. La presencia de una herramienta o el éxito de un escáner por sí
solos no demuestran un control.

## Referencias versionadas

- [OWASP Top 10 2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/)
- [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- [ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0)
- [OWASP Agentic Skills Top 10 — revisión pública v1](https://owasp.org/www-project-agentic-skills-top-10/)
- [OWASP MCP Top 10 v0.1](https://owasp.org/www-project-mcp-top-10/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)

Las listas Top 10 son catálogos de riesgos y ASVS/WCAG aportan requisitos o criterios de
verificación. El mapeo orienta pruebas de Tramalia y no extiende el alcance de esas fuentes.

## Estados permitidos

- `cubierto_por_prueba`: una prueba exacta, enlazada y ejecutada demuestra el control
  dentro del alcance y las limitaciones declaradas.
- `parcial`: existe evidencia acotada, pero falta demostrar una parte del control.
- `no_aplica_justificado`: el control queda fuera del alcance y la fila documenta una
  justificación revisable.
- `pendiente_bloqueante`: no existe evidencia suficiente y el control pendiente bloquea
  cualquier afirmación de cobertura en su alcance.

Una fila sólo puede pasar a `cubierto_por_prueba` cuando enlaza la prueba exacta que pasa;
un resultado de herramienta aislado no basta. La actualización conserva el comando, la
evidencia observada y la limitación residual.

## Controles y evidencia inicial

| ID | Control | Referencias principales | Estado | Prueba/comando concreto | Limitación inicial |
|---|---|---|---|---|---|
| TRM-SEC-001 | Confinar toda ruta y rechazar traversal/symlinks fuera de raíz | [OWASP Top 10 2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/); [ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0) | pendiente_bloqueante | `uv run --no-sync pytest tests/seguridad/test_confinamiento_rutas.py -q` | Task 4 debe crear, enlazar y hacer pasar casos de traversal, rutas absolutas y symlinks fuera de raíz. |
| TRM-SEC-002 | Ejecutar procesos sin shell, con timeout y salida acotada | [ASVS v5.0.0-1.2.5](https://github.com/OWASP/ASVS/tree/v5.0.0); [MCP05](https://owasp.org/www-project-mcp-top-10/2025/MCP05-2025%E2%80%93Command-Injection%26Execution) | parcial | `uv run --no-sync pytest tests/seguridad/test_ejecucion_procesos.py -q` | Task 2 y Task 4 deben demostrar conjuntamente argumentos estructurados, ausencia de shell, timeout y cota de salida. |
| TRM-SEC-003 | Detectar secretos en historial y árbol de trabajo | [OWASP Top 10 2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/); [MCP01](https://owasp.org/www-project-mcp-top-10/) | pendiente_bloqueante | `uv run --no-sync pytest tests/seguridad/test_secretos_git.py -q` | Task 3 debe probar historial completo, árbol de trabajo y fallo cerrado ante error o resultado indeterminado. |
| TRM-SEC-004 | Fijar y verificar herramientas/artefactos externos | [OWASP Top 10 2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/); [AST02/AST07](https://owasp.org/www-project-agentic-skills-top-10/); [MCP04](https://owasp.org/www-project-mcp-top-10/) | pendiente_bloqueante | `uv run --no-sync pytest tests/seguridad/test_integridad_herramientas.py -q` | Task 1, Task 5 y Task 7 deben fijar identidades, verificar integridad y enlazar evidencia local, de build y de CI. |
| TRM-SEC-005 | Validar habilidades antes de hacerlas visibles | [AST01/AST03/AST04/AST05/AST06/AST08](https://owasp.org/www-project-agentic-skills-top-10/) | pendiente_bloqueante | `uv run --no-sync pytest tests/seguridad/test_habilidades_cuarentena.py -q` | Task 4 debe demostrar cuarentena, validación integral y promoción atómica antes de visibilidad. |
| TRM-SEC-006 | Evitar colisiones, scope creep y sobreexposición MCP | [MCP02/MCP03/MCP07/MCP09/MCP10](https://owasp.org/www-project-mcp-top-10/) | pendiente_bloqueante | `uv run --no-sync pytest tests/seguridad/test_limites_mcp.py -q` | Task 4 debe probar nombres únicos, alcance mínimo, autorización y separación de contexto/salida. |
| TRM-SEC-007 | Mantener inventario, bloqueo y auditoría de cambios | [AST09/AST10](https://owasp.org/www-project-agentic-skills-top-10/); [MCP08](https://owasp.org/www-project-mcp-top-10/) | parcial | `uv run --no-sync pytest tests/seguridad/test_inventario_seguridad.py -q` | Task 4 y Plan 03c deben consolidar inventario, lock, procedencia y registro auditable de cambios. |
| TRM-SEC-008 | Generar puertas locales reproducibles y fail-closed | [ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0); [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) | pendiente_bloqueante | `uv run --no-sync pytest tests/contratos/test_puertas_seguridad.py -q` | Task 5 debe hacer reproducibles las puertas y probar bloqueo por herramienta ausente, error, timeout o evidencia incompleta. |
| TRM-SEC-009 | Verificar accesibilidad y adaptabilidad WCAG 2.2 AA | [WCAG 2.2](https://www.w3.org/TR/WCAG22/); [calidad UX/UI](https://www.w3.org/WAI/fundamentals/accessibility-usability-inclusion/) | pendiente_bloqueante | `uv run --no-sync pytest tests/interfaz/test_accesibilidad.py -q` | Task 6 debe enlazar resultados automatizados y revisión de teclado, contraste, reflow y estados comprensibles. |
| TRM-SEC-010 | Ejecutar CI de PR con privilegio mínimo y sin secretos | [OWASP Top 10 2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/); [AST02](https://owasp.org/www-project-agentic-skills-top-10/); [MCP04](https://owasp.org/www-project-mcp-top-10/) | pendiente_bloqueante | `uv run --no-sync pytest tests/contratos/test_ci_seguridad.py -q` | Task 7 debe probar permisos mínimos, acciones fijadas y ausencia de secretos para código de PR no confiable. |

## Regla de actualización

Las Tasks 1–7 deben editar sólo las filas que su evidencia cambie. Cada actualización
registra la ruta exacta de la prueba, el comando reproducible y la limitación que aún
permanece. Si una prueba se elimina, deja de ejecutarse o ya no cubre el invariante, la fila
vuelve a `parcial` o `pendiente_bloqueante`. `no_aplica_justificado` requiere una razón
específica del alcance y revisión humana; nunca se usa para ocultar una prueba faltante.
