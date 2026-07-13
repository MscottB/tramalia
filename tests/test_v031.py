"""v0.31 (R5a): versión instalada vs disponible de skills externas + actualizar una o todas.

Usa un repo git LOCAL como "remoto" (file://) para ser hermético, sin red.
"""

import subprocess
import types

import pytest

from tramalia.core import skills


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def _commit(root, msg):
    _git(root, "-c", "user.email=t@t.co", "-c", "user.name=t", "commit", "-m", msg)


def _mk_remote(tmp_path):
    remote = tmp_path / "remote-skill"
    remote.mkdir()
    r = _git(remote, "init", "-b", "main")
    if r.returncode != 0:  # git viejo sin -b
        _git(remote, "init")
    (remote / "SKILL.md").write_text("v1", encoding="utf-8")
    _git(remote, "add", "-A")
    _commit(remote, "v1")
    return remote


def _project_with_skill(tmp_path, remote):
    tr = tmp_path / "proj"
    (tr / ".tramalia").mkdir(parents=True)
    (tr / ".tramalia" / "skills.toml").write_text(
        f'[[skill]]\nname = "myskill"\nsource = "{remote.as_uri()}"\n', encoding="utf-8"
    )
    return tr


def _has_git():
    import shutil

    return shutil.which("git") is not None


pytestmark = pytest.mark.skipif(not _has_git(), reason="requiere git")


# ---------------------------------------------------------------- only filter
def test_sync_only_inexistente_no_hace_nada(tmp_path):
    remote = _mk_remote(tmp_path)
    proj = _project_with_skill(tmp_path, remote)
    assert skills.sync_skills(proj, only="no-existe") == []


def test_sync_only_clona_solo_esa(tmp_path):
    remote = _mk_remote(tmp_path)
    proj = _project_with_skill(tmp_path, remote)
    res = skills.sync_skills(proj, only="myskill")
    assert res == [("myskill", "clonada")]
    assert (proj / ".tramalia" / "skills" / "myskill" / "SKILL.md").exists()


# ---------------------------------------------------------------- versión instalada
def test_installed_ref_tras_clonar(tmp_path):
    remote = _mk_remote(tmp_path)
    proj = _project_with_skill(tmp_path, remote)
    skills.sync_skills(proj)
    ref = skills.installed_ref(proj, "myskill")
    assert ref and len(ref) == 7  # SHA corto


def test_installed_ref_none_si_no_esta(tmp_path):
    remote = _mk_remote(tmp_path)
    proj = _project_with_skill(tmp_path, remote)
    assert skills.installed_ref(proj, "myskill") is None


# ---------------------------------------------------------------- instalada vs disponible
def test_external_status_al_dia_y_luego_actualizable(tmp_path):
    remote = _mk_remote(tmp_path)
    proj = _project_with_skill(tmp_path, remote)
    skills.sync_skills(proj)

    # recién clonada: al día (local == remoto)
    st = {s["name"]: s for s in skills.external_status(proj, check_remote=True)}["myskill"]
    assert st["installed"] and st["installed_ref"] == st["available_ref"]
    assert st["update"] is False

    # nuevo commit en el remoto → hay actualización disponible
    (remote / "SKILL.md").write_text("v2", encoding="utf-8")
    _git(remote, "add", "-A")
    _commit(remote, "v2")
    st2 = {s["name"]: s for s in skills.external_status(proj, check_remote=True)}["myskill"]
    assert st2["update"] is True
    assert st2["installed_ref"] != st2["available_ref"]


def test_external_status_sin_remote_es_local(tmp_path):
    remote = _mk_remote(tmp_path)
    proj = _project_with_skill(tmp_path, remote)
    skills.sync_skills(proj)
    st = {s["name"]: s for s in skills.external_status(proj)}["myskill"]
    assert st["installed_ref"] is not None  # local, rápido
    assert st["available_ref"] is None  # no se consultó el remoto
    assert st["update"] is False


# ---------------------------------------------------------------- CLI
def test_cli_skills_outdated(tmp_path, monkeypatch):
    remote = _mk_remote(tmp_path)
    proj = _project_with_skill(tmp_path, remote)
    skills.sync_skills(proj)
    monkeypatch.chdir(proj)
    from tramalia.cli import commands

    args = types.SimpleNamespace(action="outdated", name=None)
    assert commands.cmd_skills(args) == 0


def test_cli_skills_sync_una(tmp_path, monkeypatch):
    remote = _mk_remote(tmp_path)
    proj = _project_with_skill(tmp_path, remote)
    monkeypatch.chdir(proj)
    from tramalia.cli import commands

    args = types.SimpleNamespace(action="sync", name="myskill")
    assert commands.cmd_skills(args) == 0
    assert (proj / ".tramalia" / "skills" / "myskill").exists()
