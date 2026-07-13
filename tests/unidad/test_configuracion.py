import json
from pathlib import Path

from tramalia.core import configuracion


def test_guardar_configuracion_publica_json_con_replace_atomico(tmp_path, monkeypatch) -> None:
    publicaciones: list[tuple[Path, Path]] = []
    reemplazar_real = Path.replace

    def reemplazar(origen: Path, destino: Path) -> Path:
        publicaciones.append((origen, Path(destino)))
        return reemplazar_real(origen, destino)

    monkeypatch.setattr(Path, "replace", reemplazar)

    assert configuracion.guardar_configuracion(tmp_path, {"mode": "team"})

    ruta = tmp_path / ".tramalia" / "config.json"
    assert json.loads(ruta.read_text(encoding="utf-8")) == {"mode": "team"}
    assert len(publicaciones) == 1
    temporal, destino = publicaciones[0]
    assert destino == ruta
    assert temporal.parent == destino.parent
    assert ".tmp-" in temporal.name
    assert not temporal.exists()


def test_modo_trabajo_solo_acepta_team_exacto(tmp_path) -> None:
    assert configuracion.modo_trabajo(tmp_path) == "local-first"
    ruta = tmp_path / ".tramalia" / "config.json"
    ruta.parent.mkdir()
    ruta.write_text('{"mode": "TEAM"}', encoding="utf-8")
    assert configuracion.modo_trabajo(tmp_path) == "local-first"
    ruta.write_text('{"mode": "team"}', encoding="utf-8")
    assert configuracion.modo_trabajo(tmp_path) == "team"
