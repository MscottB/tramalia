# Contribuir a Tramalia

¡Gracias por tu interés! Tramalia es una **capa repo-first de gobierno y evidencia** para desarrollo con múltiples agentes IA. Estas son las pautas para contribuir.

## Filosofía (léela antes de proponer features)

- **No reimplementar, orquestar.** Si una herramienta externa ya hace algo bien (memoria, compresión, navegación de código…), Tramalia la *detecta, cablea e invoca* — no la reescribe.
- **El núcleo es chico y standalone.** `init`, `doctor`, `close`, `log`, `evidence`, `handoff` corren **solo con Python**. Las features que dependen de herramientas externas van como **interop opcional** que degrada con gracia.
- **No tocar el moat.** Los `*-output.txt` crudos y `metadata.json` son la evidencia oficial; ningún artefacto derivado puede modificarlos, reemplazarlos ni omitirlos.

## Cómo empezar

```bash
git clone https://github.com/MscottB/tramalia.git
cd tramalia
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,pretty,mcp]"
pytest
```

## Flujo de trabajo

1. Abre un **issue** para discutir cambios grandes antes de codear.
2. Para cambios chicos, envía un **PR** directo.
3. Antes de enviar: `pytest` en verde y, si tocaste docs, `mkdocs build` sin errores.
4. Mantén el estilo y la densidad del código existente (comentarios al mismo nivel, nombres en el mismo idioma).
5. Si agregas una herramienta externa: regístrala en `tramalia/core/tools.py`, documéntala en `docs/interop-*.md`, y **no** la hagas obligatoria.

## Tests

- Los tests viven en `tests/` y usan `pytest` (nombres en español).
- Toda lógica nueva del núcleo debe venir con su test.
- El test guardián `test_close_conserva_salidas_crudas` protege el moat: no lo debilites.

## Licencia

Al contribuir, aceptas que tu aporte se licencie bajo **Apache-2.0** (ver [`LICENSE`](LICENSE)).
