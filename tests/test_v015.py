"""v0.15: matriz de gates por stack + dialectos SQL + detección fina."""

from tramalia.core.detect import detect_stack, enabled_features
from tramalia.core.scaffold import build_mise_toml, build_sqlfluff, scaffold
from tramalia.core.tools import REGISTRY, relevant_tools


def _mise(stacks):
    return build_mise_toml({"stacks": stacks, "features": enabled_features(stacks)})


# ---------------------------------------------------------------- gate matrix
def test_gates_go():
    mise = _mise(["go"])
    assert "go build ./..." in mise and "go test ./..." in mise


def test_gates_rust():
    mise = _mise(["rust"])
    assert "cargo build" in mise and "cargo test" in mise


def test_gates_maven_y_gradle():
    assert "mvn -B compile" in _mise(["java", "maven"])
    assert "gradle build" in _mise(["gradle"])


def test_next_es_frontend_y_activa_ux():
    stacks = ["node", "next"]
    assert "ux" in enabled_features(stacks)
    assert "npm run build" in _mise(stacks)


# ---------------------------------------------------------------- detección fina
def test_detecta_next_nest_tailwind(tmp_path):
    (tmp_path / "next.config.js").write_text("module.exports={}", encoding="utf-8")
    (tmp_path / "nest-cli.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tailwind.config.js").write_text("module.exports={}", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    stack = detect_stack(tmp_path)
    assert {"next", "nest", "tailwind", "node"} <= set(stack)


def test_detecta_sqlserver_por_csproj(tmp_path):
    (tmp_path / "Api.csproj").write_text(
        '<Project><ItemGroup><PackageReference Include="Microsoft.Data.SqlClient"/>'
        "</ItemGroup></Project>", encoding="utf-8")
    stack = detect_stack(tmp_path)
    assert "sqlserver" in stack and "dotnet" in stack
    assert "database" in enabled_features(stack)


# ---------------------------------------------------------------- .sqlfluff
def test_sqlfluff_postgres():
    out = build_sqlfluff({"stacks": ["postgres"]})
    assert "dialect = postgres" in out


def test_sqlfluff_sqlserver_es_tsql():
    out = build_sqlfluff({"stacks": ["sqlserver"]})
    assert "dialect = tsql" in out


def test_sqlfluff_none_sin_sql():
    assert build_sqlfluff({"stacks": ["python"]}) is None


def test_sqlfluff_multimotor_comenta_secundario():
    # el stack real del usuario: Postgres + SQL Server en el mismo repo.
    # Prioridad databricks > sqlserver(tsql) > postgres: aquí primario tsql.
    out = build_sqlfluff({"stacks": ["postgres", "sqlserver"]})
    assert "dialect = tsql" in out              # primario (SQL Server)
    assert "postgres" in out                    # guía para el secundario


def test_init_genera_sqlfluff_para_stack_sql(tmp_path):
    scaffold(tmp_path, {"project_name": "d", "stacks": ["dotnet", "postgres"],
                        "features": enabled_features(["dotnet", "postgres"]),
                        "primary_agent": "codex", "reviewer_agent": "claude"})
    assert (tmp_path / ".sqlfluff").is_file()


# ---------------------------------------------------------------- doctor stacks
def test_doctor_surface_toolchains_por_stack():
    keys = {t.key for t in REGISTRY if t.category == "stack"}
    assert {"go", "cargo", "mvn", "gradle"} <= keys
    # go solo aparece si el stack lo usa
    assert "go" in {t.key for t in relevant_tools(["go"], enabled_features(["go"]))}
    assert "go" not in {t.key for t in relevant_tools(["python"], enabled_features(["python"]))}
