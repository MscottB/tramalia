"""v0.32 (R5b/F1): init detecta agentes instalados en vez de codex/claude fijos.

Antes, `tramalia init` grababa siempre primary="codex", reviewer="claude" en
config.json sin importar qué había instalado — el tab Cierre precargaba esos
nombres sin relación con la máquina real. Ahora se detecta con integraciones.sondear().
"""

import json
import types

from tramalia.core import integraciones
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _herramienta(clave):
    return next(herramienta for herramienta in integraciones.REGISTRO if herramienta.clave == clave)


# --------------------------------------------------- detectar_agentes_predeterminados
def test_dos_agentes_detectados_uno_ejecuta_otro_revisa(monkeypatch):
    def sondeo_falso(herramienta, limite_segundos=8.0):
        return integraciones.EstadoHerramienta(
            herramienta,
            presente=herramienta.clave in ("claude", "codex"),
        )

    monkeypatch.setattr(integraciones, "sondear", sondeo_falso)
    primary, reviewer = integraciones.detectar_agentes_predeterminados()
    assert primary == "claude"  # primero en el orden de preferencia
    assert reviewer == "codex"
    assert primary != reviewer  # cross-review real


def test_un_solo_agente_se_usa_para_ambos(monkeypatch):
    def sondeo_falso(herramienta, limite_segundos=8.0):
        return integraciones.EstadoHerramienta(
            herramienta,
            presente=herramienta.clave == "opencode",
        )

    monkeypatch.setattr(integraciones, "sondear", sondeo_falso)
    primary, reviewer = integraciones.detectar_agentes_predeterminados()
    assert primary == reviewer == "opencode"


def test_ningun_agente_cae_a_ejemplo_editable(monkeypatch):
    monkeypatch.setattr(
        integraciones,
        "sondear",
        lambda herramienta, limite_segundos=8.0: integraciones.EstadoHerramienta(
            herramienta,
            presente=False,
        ),
    )
    assert integraciones.detectar_agentes_predeterminados() == ("codex", "claude")


def test_antigravity_ide_y_2_excluidos_de_deteccion(monkeypatch):
    # apps de escritorio: no pueden ejecutar `close` por shell, no deben elegirse
    def sondeo_falso(herramienta, limite_segundos=8.0):
        return integraciones.EstadoHerramienta(
            herramienta,
            presente=herramienta.clave in ("antigravity-ide", "antigravity-2"),
        )

    monkeypatch.setattr(integraciones, "sondear", sondeo_falso)
    assert integraciones.detectar_agentes_predeterminados() == ("codex", "claude")


# ---------------------------------------------------------------- init usa la detección
def test_init_config_json_usa_agentes_detectados(tmp_path, monkeypatch):
    # comando_inicializar importa `detectar_agentes_predeterminados` dentro de la función:
    # el cuerpo de la función: parchar el atributo del módulo alcanza.
    monkeypatch.setattr(
        integraciones,
        "detectar_agentes_predeterminados",
        lambda: ("opencode", "opencode"),
    )
    monkeypatch.chdir(tmp_path)
    from tramalia.cli import comandos

    comandos.comando_inicializar(types.SimpleNamespace())
    data = json.loads((tmp_path / ".tramalia" / "config.json").read_text(encoding="utf-8"))
    assert data["agents"]["primary"] == "opencode"
    assert data["agents"]["reviewer"] == "opencode"


def test_upgrade_no_pisa_config_existente(tmp_path, monkeypatch):
    # upgrade nunca toca un config.json ya existente (idempotencia del scaffold)
    scaffold(
        tmp_path,
        {
            "project_name": "demo",
            "stacks": ["python"],
            "features": enabled_features(["python"]),
            "primary_agent": "claude",
            "reviewer_agent": "codex",
        },
    )
    cfg = tmp_path / ".tramalia" / "config.json"
    original = cfg.read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    from tramalia.cli import comandos

    comandos.comando_actualizar_proyecto(types.SimpleNamespace())
    assert cfg.read_text(encoding="utf-8") == original
