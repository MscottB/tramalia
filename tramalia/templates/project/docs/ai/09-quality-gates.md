# 09 — Quality gates

## Gates de este proyecto
Definidos como tasks en `mise.toml`; `tramalia close` los ejecuta con enforcement.

- Build: · Tests: · Lint/Format: · Security: · Database: · UX/UI:

## Criterio de cierre
Una tarea solo se cierra si los gates aplicables pasan, o si la excepción queda
documentada (`--allow-fail` + nota en `risks.md` del evidence pack).
