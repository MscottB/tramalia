# Arquitectura de pruebas

La suite se organiza por comportamiento, no por número de versión.

- `unidad/`: lógica pura.
- `contratos/`: formatos y APIs públicas.
- `integracion/`: filesystem, Git y procesos.
- `interfaz/`: flujos públicos de Textual.
- `publicacion/`: wheel y lanzamiento.

Los archivos históricos `test_v*.py` se migran cuando el plan del subsistema
correspondiente refactoriza ese comportamiento. Ningún plan elimina una regresión
sin reemplazarla por un contrato observable y registrar la decisión en
`tests/AUDITORIA.md`.
