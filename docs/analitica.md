# Proyectos de analítica (Python · Databricks)

Tramalia gobierna igual de bien un proyecto de datos que uno de software — y de hecho los equipos de analítica suelen ser los que **menos evidencia dejan** (¿qué job corrió?, ¿con qué validación?, ¿quién lo cerró?). Aquí la convención + `close` aportan justo eso.

## Qué detecta

| Señal en el repo | Stack detectado | Efecto |
|---|---|---|
| `pyproject.toml` / `requirements.txt` | `python` | gates `pytest` + `ruff` |
| `databricks.yml` (Asset Bundles) | `databricks` | gate **`bundle`** → `databricks bundle validate` |
| `*.ipynb` | `notebooks` | el gate lint agrega **`nbstripout --verify`** |
| `*.sql` / migraciones | `postgres`-like | gate `database` → SQLFluff, **con `--dialect databricks`** si hay bundle |

## Los gates de datos, explicados

- **`bundle`** (`databricks bundle validate`): valida la definición del bundle (jobs, pipelines, targets) *antes* de desplegar — el equivalente a "compila" en el mundo Databricks. Requiere el [Databricks CLI](https://docs.databricks.com/dev-tools/cli/install) (`tramalia doctor` lo detecta).
- **`nbstripout --verify`**: falla si algún notebook tiene **outputs sin limpiar** — outputs sucios rompen los diffs, filtran datos a git y hacen imposible la revisión. Es el gate de higiene mínimo de notebooks.
- **SQLFluff con dialecto databricks**: lintea tus SQL/queries con la gramática correcta (Delta, `CREATE TABLE ... USING`, etc.).

## El flujo tipo

```bash
cd mi-pipeline-datos          # repo con databricks.yml + notebooks/ + src/
pip install tramalia-cli
tramalia init                 # detecta python · databricks · notebooks
mise install                  # trae sqlfluff, semgrep… (databricks CLI: instalador oficial)

# trabajas la tarea (local o contra el workspace)…
tramalia close TASK-014 --model sonnet
```

El evidence pack de un cierre de datos queda con `bundle-output.txt` (la validación cruda del bundle), `database-output.txt` (SQLFluff), `lint-output.txt` (ruff + verificación de notebooks) — **auditoría real para pipelines**, lo que un `git log` nunca te da.

## Entorno local vs. Databricks

- **Local**: todo lo anterior corre sin workspace (validate es estático; pytest/ruff/nbstripout son locales).
- **Contra Databricks**: `bundle validate` usa tu autenticación del CLI (`databricks auth login`) — Tramalia no toca credenciales, como siempre.
- Los **subagentes** aplican igual: el `planificador` descompone el pipeline en tareas de `specs/tasks.md`, el `ejecutor` implementa notebooks/jobs, el `revisor` lee el pack antes del deploy.

!!! note "Qué NO hace Tramalia aquí"
    No orquesta jobs (eso es Databricks Workflows/Airflow), no valida calidad de *datos* (eso es Great Expectations/dbt tests — puedes agregarlos como comandos en el gate `test` de tu `mise.toml`). Tramalia gobierna el **código y el cierre** del trabajo, con evidencia.
