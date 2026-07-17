# Excepciones de Gitleaks

## Alcance de los escaneos

`gitleaks git` inspecciona los commits del historial completo. `gitleaks dir .`
inspecciona por separado el árbol de trabajo, incluidos los archivos sin confirmar:

```powershell
gitleaks dir . --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
```

Ambos escaneos son obligatorios y ninguno sustituye al otro. El límite de 10 MB
evita consumo de memoria sin límite; todo archivo fuente que lo supere requiere
una revisión explícita separada.

## Criterio para excepciones

Una credencial plausible se revoca y elimina, incluso si sólo aparece en el
historial. Nunca se registra como excepción. Los ejemplos inseguros se cambian
por valores claramente ficticios. Sólo un falso positivo histórico, validado
como no sensible, puede añadirse a `.gitleaksignore` mediante su fingerprint
individual.

Cada fingerprint activo debe tener una fila con su ruta y regla exactas, una
razón verificable y una fecha de revisión en formato `AAAA-MM-DD`.

| Fingerprint | Ruta | Regla | Razon | Revision |
| --- | --- | --- | --- | --- |

No hay excepciones activas.
