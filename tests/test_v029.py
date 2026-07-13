"""v0.29: higiene de repositorio para habilidades externas reproducibles."""

import subprocess

from tramalia.core import habilidades
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _ejecutar_git(raiz, *argumentos):
    return subprocess.run(
        ["git", "-C", str(raiz), *argumentos],
        capture_output=True,
        text=True,
        check=False,
    )


def _crear_repositorio_git(tmp_path):
    _ejecutar_git(tmp_path, "init")
    _ejecutar_git(tmp_path, "config", "user.email", "t@t.co")
    _ejecutar_git(tmp_path, "config", "user.name", "t")
    return tmp_path


def _inicializar(tmp_path):
    scaffold(
        tmp_path,
        {
            "project_name": "demo",
            "stacks": ["python"],
            "features": enabled_features(["python"]),
            "primary_agent": "codex",
            "reviewer_agent": "claude",
        },
    )
    return tmp_path


def test_gitignore_se_crea_si_no_existe(tmp_path):
    assert habilidades.asegurar_gitignore_habilidades(tmp_path) == "creado"
    texto = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".tramalia/habilidades/*/" in texto
    assert "!.tramalia/habilidades/[0-9][0-9]-*/" in texto


def test_gitignore_append_a_existente_sin_pisar(tmp_path):
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\n", encoding="utf-8")
    assert habilidades.asegurar_gitignore_habilidades(tmp_path) == "adaptado"
    texto = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in texto and "*.log" in texto
    assert ".tramalia/habilidades/*/" in texto


def test_gitignore_es_idempotente(tmp_path):
    habilidades.asegurar_gitignore_habilidades(tmp_path)
    assert habilidades.asegurar_gitignore_habilidades(tmp_path) == "existe"
    texto = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert texto.count(".tramalia/habilidades/*/") == 1


def test_scaffold_escribe_gitignore(tmp_path):
    resultados = dict(
        scaffold(
            tmp_path,
            {
                "project_name": "demo",
                "stacks": ["python"],
                "features": enabled_features(["python"]),
                "primary_agent": "codex",
                "reviewer_agent": "claude",
            },
        )
    )
    assert resultados.get(".gitignore") in ("creado", "adaptado")
    assert (tmp_path / ".gitignore").exists()


def test_patron_excluye_externas_conserva_propias(tmp_path):
    _crear_repositorio_git(tmp_path)
    _inicializar(tmp_path)
    externa = tmp_path / ".tramalia" / "habilidades" / "ponytail"
    externa.mkdir(parents=True)
    (externa / "SKILL.md").write_text("x", encoding="utf-8")

    ignorada = _ejecutar_git(tmp_path, "check-ignore", ".tramalia/habilidades/ponytail/")
    propia = _ejecutar_git(tmp_path, "check-ignore", ".tramalia/habilidades/01-spec-governance/")
    assert ignorada.returncode == 0
    assert propia.returncode == 1


def test_detecta_externas_ya_commiteadas(tmp_path):
    _crear_repositorio_git(tmp_path)
    _inicializar(tmp_path)
    directorio = tmp_path / ".tramalia" / "habilidades" / "superpowers"
    directorio.mkdir(parents=True)
    (directorio / "SKILL.md").write_text("y", encoding="utf-8")
    _ejecutar_git(tmp_path, "add", "-f", ".tramalia/habilidades/superpowers/SKILL.md")
    _ejecutar_git(
        tmp_path,
        "-c",
        "user.email=t@t.co",
        "-c",
        "user.name=t",
        "commit",
        "-m",
        "x",
    )

    rastreadas = habilidades.habilidades_externas_rastreadas(tmp_path)

    assert "superpowers" in rastreadas
    assert not any(nombre.startswith(("00-", "01-", "02-")) for nombre in rastreadas)


def test_sin_git_no_revienta(tmp_path):
    _inicializar(tmp_path)
    assert habilidades.habilidades_externas_rastreadas(tmp_path) == ()
