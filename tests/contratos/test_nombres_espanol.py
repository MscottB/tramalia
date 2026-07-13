from importlib import import_module
from pathlib import Path


def test_modulos_finales_en_espanol_y_antiguos_ausentes() -> None:
    raiz = Path(__file__).parents[2]
    nuevos = (
        "tramalia.core.integraciones",
        "tramalia.core.procesos",
        "tramalia.core.habilidades",
        "tramalia.core.contexto",
        "tramalia.core.proveedor_contexto",
        "tramalia.core.configuracion",
        "tramalia.core.tablero",
        "tramalia.cli.comandos",
        "tramalia.cli.renderizado",
        "tramalia.interfaz_terminal",
    )
    for modulo in nuevos:
        import_module(modulo)
    assert (raiz / "tramalia/templates/project/.tramalia/habilidades.toml").is_file()
    assert (raiz / "tramalia/templates/project/.tramalia/habilidades").is_dir()
    antiguos = (
        "tramalia/core/tools.py",
        "tramalia/core/proc.py",
        "tramalia/core/skills.py",
        "tramalia/core/context.py",
        "tramalia/core/context_backend.py",
        "tramalia/core/project.py",
        "tramalia/cli/commands.py",
        "tramalia/cli/render.py",
        "tramalia/tui.py",
        "tramalia/templates/project/.tramalia/skills.toml",
        "tramalia/templates/project/.tramalia/skills",
    )
    assert all(not (raiz / ruta).exists() for ruta in antiguos)
