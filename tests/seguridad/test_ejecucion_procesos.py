"""Regresiones para procesos externos con limites explicitos."""

from __future__ import annotations

import subprocess

from scripts import build_offline_docs
from tramalia.cli import comandos
from tramalia.core import doctor
from tramalia.core.integraciones import EstadoHerramienta, Herramienta


def _habilitar_tty(monkeypatch) -> None:
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)


def _reporte_con_mise() -> doctor.Report:
    herramienta = Herramienta(
        clave="mise",
        comando="mise",
        rol="gestor",
        categoria="bootstrap",
    )
    return doctor.Report(
        stack=[],
        features=(),
        statuses=[EstadoHerramienta(herramienta, presente=True)],
    )


def test_build_offline_acota_timeout_y_limpia_configuracion_temporal(
    tmp_path, monkeypatch, capsys
) -> None:
    raiz = tmp_path / "repo"
    raiz.mkdir()
    configuracion = raiz / "mkdocs.yml"
    configuracion.write_text("plugins:\n  - search\n", encoding="utf-8")
    salida = raiz / "tramalia-docs-offline.zip"
    opciones_recibidas: dict[str, object] = {}

    def ejecutar_timeout(comando, **opciones):
        opciones_recibidas.update(opciones)
        raise subprocess.TimeoutExpired(comando, opciones.get("timeout", -1))

    monkeypatch.setattr(build_offline_docs, "ROOT", raiz)
    monkeypatch.setattr(build_offline_docs, "CONFIG", configuracion)
    monkeypatch.setattr(build_offline_docs, "OUT_ZIP", salida)
    monkeypatch.setattr(build_offline_docs.subprocess, "run", ejecutar_timeout)

    assert build_offline_docs.main() == 124
    assert opciones_recibidas["timeout"] == 300
    diagnostico = capsys.readouterr().err
    assert diagnostico and "300" in diagnostico
    assert not (raiz / ".mkdocs.offline.tmp.yml").exists()


def test_oferta_pip_convierte_timeout_en_error_visible(monkeypatch) -> None:
    _habilitar_tty(monkeypatch)
    monkeypatch.setattr(comandos.menu, "pedir_texto", lambda *_a, **_k: "s")
    opciones_recibidas: dict[str, object] = {}
    errores: list[str] = []

    def ejecutar_timeout(comando, **opciones):
        opciones_recibidas.update(opciones)
        raise subprocess.TimeoutExpired(comando, opciones.get("timeout", -1))

    monkeypatch.setattr(subprocess, "run", ejecutar_timeout)
    monkeypatch.setattr(comandos.renderizado, "error", lambda mensaje: errores.append(str(mensaje)))

    assert comandos._ofrecer_instalar("textual", "el dashboard TUI") is False
    assert opciones_recibidas["timeout"] == 600
    assert errores


def test_doctor_fix_convierte_timeout_en_false(monkeypatch) -> None:
    opciones_recibidas: dict[str, object] = {}

    def ejecutar_timeout(comando, **opciones):
        opciones_recibidas.update(opciones)
        raise subprocess.TimeoutExpired(comando, opciones.get("timeout", -1))

    monkeypatch.setattr(doctor.subprocess, "run", ejecutar_timeout)

    assert doctor.fix(_reporte_con_mise()) is False
    assert opciones_recibidas["timeout"] == 600
