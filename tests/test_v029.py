"""v0.29 (R3, parte A): higiene de repo — skills externas fuera de git, sin perderlas.

- init crea/actualiza .gitignore (idempotente) para excluir skills externas y
  conservar las propias NN-* (el manifiesto skills.toml las re-hidrata).
- detección de externas YA commiteadas (el .gitignore no las destrackea).
"""

import subprocess

from tramalia.core import skills
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def _git_repo(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "t@t.co")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path


def _init(tmp_path):
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


# ---------------------------------------------------------------- .gitignore
def test_gitignore_se_crea_si_no_existe(tmp_path):
    assert skills.ensure_skills_gitignore(tmp_path) == "creado"
    txt = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".tramalia/skills/*/" in txt
    assert "!.tramalia/skills/[0-9][0-9]-*/" in txt


def test_gitignore_append_a_existente_sin_pisar(tmp_path):
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\n", encoding="utf-8")
    assert skills.ensure_skills_gitignore(tmp_path) == "adaptado"
    txt = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in txt and "*.log" in txt  # lo del usuario intacto
    assert ".tramalia/skills/*/" in txt


def test_gitignore_es_idempotente(tmp_path):
    skills.ensure_skills_gitignore(tmp_path)
    assert skills.ensure_skills_gitignore(tmp_path) == "existe"
    txt = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert txt.count(".tramalia/skills/*/") == 1  # no duplica el bloque


def test_scaffold_escribe_gitignore(tmp_path):
    results = dict(
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
    assert results.get(".gitignore") in ("creado", "adaptado")
    assert (tmp_path / ".gitignore").exists()


# ---------------------------------------------------------------- patrón real con git
def test_patron_excluye_externas_conserva_propias(tmp_path):
    _git_repo(tmp_path)
    _init(tmp_path)
    (tmp_path / ".tramalia" / "skills" / "ponytail").mkdir(parents=True)
    (tmp_path / ".tramalia" / "skills" / "ponytail" / "SKILL.md").write_text("x", encoding="utf-8")
    # externa ignorada; propia numerada NO
    ext = _git(tmp_path, "check-ignore", ".tramalia/skills/ponytail/")
    own = _git(tmp_path, "check-ignore", ".tramalia/skills/01-spec-governance/")
    assert ext.returncode == 0  # ponytail: ignorada
    assert own.returncode == 1  # 01-*: rastreada (no ignorada)


# ---------------------------------------------------------------- detección trackeadas
def test_detecta_externas_ya_commiteadas(tmp_path):
    _git_repo(tmp_path)
    _init(tmp_path)
    d = tmp_path / ".tramalia" / "skills" / "superpowers"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("y", encoding="utf-8")
    _git(tmp_path, "add", "-f", ".tramalia/skills/superpowers/SKILL.md")  # forzar pese al ignore
    _git(tmp_path, "-c", "user.email=t@t.co", "-c", "user.name=t", "commit", "-m", "x")
    tracked = skills.tracked_external_skills(tmp_path)
    assert "superpowers" in tracked
    assert not any(n.startswith(("00-", "01-", "02-")) for n in tracked)  # propias no


def test_sin_git_no_revienta(tmp_path):
    # sin repo git, la detección devuelve lista vacía (no error)
    _init(tmp_path)
    assert skills.tracked_external_skills(tmp_path) == []
