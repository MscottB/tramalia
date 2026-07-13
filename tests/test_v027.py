"""v0.27 (R1): installer correcto + labels.

- engram se instala encadenado tras Go (refresh de PATH del proceso).
- labels de agentes dicen "CLI" para no confundir con apps de escritorio.
- OpenClaw automatizable por npm; Hermes manual con su comando real.
- Antigravity: 3 superficies (CLI/agy por winget, IDE y 2.0 detectables por id_winget).
"""

import os

from tramalia.core import installer
from tramalia.core.integraciones import REGISTRO


def _herramienta(clave):
    return next(herramienta for herramienta in REGISTRO if herramienta.clave == clave)


# ---------------------------------------------------------------- labels CLI
def test_labels_agentes_dicen_cli():
    assert "CLI" in _herramienta("claude").rol
    assert "CLI" in _herramienta("codex").rol
    assert "agy" in _herramienta("antigravity").rol  # comando explícito


# ---------------------------------------------------------------- openclaw / hermes
def test_openclaw_automatizable_via_npm():
    opts = installer.options_for(_herramienta("openclaw"))
    npm = next((o for o in opts if o.method == "npm"), None)
    assert npm is not None and npm.requires == "npm"
    assert "openclaw" in npm.args[-1]


def test_hermes_manual_con_comando_real():
    # Hermes solo instala por script → manual, pero con el comando exacto (no "ver docs")
    opts = installer.options_for(_herramienta("hermes"))
    assert opts and not any(o.auto for o in opts)
    assert "hermes-agent.nousresearch.com/install.sh" in opts[0].display


# ---------------------------------------------------------------- antigravity x3
def test_tres_superficies_antigravity_en_registro():
    keys = {herramienta.clave for herramienta in REGISTRO}
    assert {"antigravity", "antigravity-ide", "antigravity-2"} <= keys
    # las apps de escritorio se detectan por winget_id (no tienen comando en PATH)
    assert _herramienta("antigravity-ide").id_winget == "Google.AntigravityIDE"
    assert _herramienta("antigravity-2").id_winget == "Google.Antigravity"
    assert _herramienta("antigravity").id_winget == ""  # el CLI sí tiene comando (agy)


def test_antigravity_ide_y_2_winget_en_windows():
    for key in ("antigravity-ide", "antigravity-2"):
        win = installer.options_for(_herramienta(key), os_name="windows")
        assert win and win[0].method == "winget"


# ---------------------------------------------------------------- winget detección
def test_probe_detecta_por_winget_id(monkeypatch):
    import tramalia.core.integraciones as integraciones_mod

    # simula que winget existe y que 'Google.AntigravityIDE' aparece en el listado
    monkeypatch.setattr(
        integraciones_mod.shutil, "which", lambda c: "winget" if c == "winget" else None
    )
    integraciones_mod._ESTADO_WINGET.update(
        {
            "cargado": True,
            "texto": "Name  Id  Version\nAntigravity IDE  Google.AntigravityIDE  2.0.4",
        }
    )
    estado = integraciones_mod.sondear(_herramienta("antigravity-ide"))
    assert estado.presente is True
    integraciones_mod._ESTADO_WINGET.update({"cargado": False, "texto": ""})


def test_probe_winget_id_ausente_es_faltante(monkeypatch):
    import tramalia.core.integraciones as integraciones_mod

    monkeypatch.setattr(
        integraciones_mod.shutil, "which", lambda c: "winget" if c == "winget" else None
    )
    integraciones_mod._ESTADO_WINGET.update({"cargado": True, "texto": "Name  Id  Version\n"})
    estado = integraciones_mod.sondear(_herramienta("antigravity-2"))
    assert estado.presente is False
    integraciones_mod._ESTADO_WINGET.update({"cargado": False, "texto": ""})


# ---------------------------------------------------------------- PATH refresh
def test_refresh_runtime_path_agrega_dirs_existentes(monkeypatch, tmp_path):
    gobin = tmp_path / "go" / "bin"
    gobin.mkdir(parents=True)
    monkeypatch.setattr(installer, "known_runtime_bin_dirs", lambda: [gobin])
    monkeypatch.setenv("PATH", "")
    installer.refresh_runtime_path()
    assert str(gobin) in os.environ["PATH"]
    # idempotente: no lo duplica
    installer.refresh_runtime_path()
    assert os.environ["PATH"].count(str(gobin)) == 1


def test_engram_bloqueado_por_go_lo_marca_como_runtime(monkeypatch):
    # hermético: simulamos Go ausente (el equipo real puede tenerlo instalado).
    monkeypatch.setattr(installer.shutil, "which", lambda c: None if c == "go" else "x")
    auto, manual, offers = installer.plan_for([_herramienta("engram")], os_name="windows")
    manual_map = {cmd: rt for cmd, _d, rt in manual}
    assert manual_map.get("engram") == "go"  # bloqueado por el runtime Go
    assert any("engram" in enables for _n, _o, enables in offers)  # Go lo desbloquea
