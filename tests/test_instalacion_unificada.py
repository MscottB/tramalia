"""Instalación unificada: pretty incluido por defecto + auto-oferta de extras."""

import tomllib
from pathlib import Path

from tramalia.cli import comandos


def _pyproject():
    raiz = Path(__file__).resolve().parent.parent
    return tomllib.loads((raiz / "pyproject.toml").read_text(encoding="utf-8"))


def test_pretty_incluido_por_defecto():
    proyecto = _pyproject()["project"]
    deps = " ".join(proyecto["dependencies"])
    assert "rich" in deps and "questionary" in deps
    # el alias queda vacío por compatibilidad; nadie que lo use se rompe
    assert proyecto["optional-dependencies"]["pretty"] == []


def test_alias_full_existe():
    extras = _pyproject()["project"]["optional-dependencies"]
    full = " ".join(extras["full"])
    assert "mcp" in full and "textual" in full


def test_oferta_sin_tty_no_pregunta(capsys):
    # en pytest no hay TTY: debe imprimir el hint y devolver False, sin colgarse
    assert comandos._ofrecer_instalar("textual", "el dashboard TUI") is False


def test_oferta_rechazada_no_instala(monkeypatch):
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(comandos.menu, "pedir_texto", lambda *a, **k: "n")
    llamado = []
    monkeypatch.setattr("subprocess.run", lambda *a, **k: llamado.append(a))
    assert comandos._ofrecer_instalar("textual", "el dashboard TUI") is False
    assert not llamado  # nunca se invocó pip


def test_oferta_aceptada_instala(monkeypatch):
    import subprocess
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(comandos.menu, "pedir_texto", lambda *a, **k: "s")
    invocaciones = []

    def ejecutar_falso(comando, **opciones):
        invocaciones.append((comando, opciones))
        return subprocess.CompletedProcess(comando, 0)

    monkeypatch.setattr(subprocess, "run", ejecutar_falso)
    assert comandos._ofrecer_instalar("textual", "el dashboard TUI") is True
    assert invocaciones
    comando, opciones = invocaciones[0]
    assert comando[-2:] == ["install", "textual"]
    assert opciones["timeout"] == 600
