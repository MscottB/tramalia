from pathlib import Path

import pytest

from tramalia.core import habilidades
from tramalia.core.errores import ErrorConfiguracionHabilidades
from tramalia.core.habilidades import agregar_habilidad, bloque_gitignore, leer_habilidades
from tramalia.core.procesos import ResultadoProceso

pytestmark = pytest.mark.integracion


def test_manifiesto_toml_invalido_falla_cerrado_sin_exponer_contenido(
    tmp_path: Path,
) -> None:
    directorio = tmp_path / ".tramalia"
    directorio.mkdir()
    secreto = "token=valor-que-no-debe-aparecer"
    ruta = directorio / "habilidades.toml"
    ruta.write_text(f"[[habilidad]\n{secreto}\n", encoding="utf-8")

    with pytest.raises(ErrorConfiguracionHabilidades) as captura:
        leer_habilidades(tmp_path)

    error = captura.value
    assert error.ruta == Path(".tramalia/habilidades.toml")
    assert secreto not in str(error)
    assert secreto not in str(error.como_dict())


@pytest.mark.parametrize(
    ("nombre", "fuente"),
    (
        ("../../escape", "git+https://example.com/segura.git"),
        ("segura", "http://example.com/insegura.git"),
    ),
)
def test_declaracion_insegura_invalida_manifiesto_completo(
    tmp_path: Path,
    nombre: str,
    fuente: str,
) -> None:
    directorio = tmp_path / ".tramalia"
    directorio.mkdir()
    (directorio / "habilidades.toml").write_text(
        f'[[habilidad]]\nnombre = "{nombre}"\nfuente = "{fuente}"\nreferencia = "main"\n',
        encoding="utf-8",
    )

    with pytest.raises(ErrorConfiguracionHabilidades):
        leer_habilidades(tmp_path)

    assert not (tmp_path.parent / "escape").exists()


def test_manifiesto_duplicado_falla_antes_de_aplicar_solo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directorio = tmp_path / ".tramalia"
    directorio.mkdir()
    (directorio / "habilidades.toml").write_text(
        '[[habilidad]]\nnombre = "demo"\nfuente = "git+https://example.com/a.git"\n'
        'referencia = "main"\n\n[[habilidad]]\nnombre = "demo"\n'
        'fuente = "git+https://example.com/b.git"\nreferencia = "main"\n',
        encoding="utf-8",
    )
    llamadas: list[str] = []
    monkeypatch.setattr(
        habilidades,
        "git_disponible",
        lambda: llamadas.append("git") or True,
    )

    with pytest.raises(ErrorConfiguracionHabilidades, match="duplicad"):
        habilidades.sincronizar_habilidades(tmp_path, solo="demo")

    assert llamadas == []


def test_lector_normaliza_fuente_https(tmp_path: Path) -> None:
    directorio = tmp_path / ".tramalia"
    directorio.mkdir()
    (directorio / "habilidades.toml").write_text(
        '[[habilidad]]\nnombre = "demo"\nfuente = "https://example.com/demo.git"\n'
        'referencia = "main"\n',
        encoding="utf-8",
    )

    assert leer_habilidades(tmp_path)[0].fuente == "git+https://example.com/demo.git"


@pytest.mark.parametrize(
    ("fuente", "nombre"),
    (
        ("http://example.com/demo.git", None),
        ("git+https://example.com/demo.git", "../../escape"),
    ),
)
def test_agregar_habilidad_rechaza_entrada_insegura_sin_mutar(
    tmp_path: Path,
    fuente: str,
    nombre: str | None,
) -> None:
    directorio = tmp_path / ".tramalia"
    directorio.mkdir()
    ruta = directorio / "habilidades.toml"
    original = "# conservar\n"
    ruta.write_text(original, encoding="utf-8")

    assert agregar_habilidad(tmp_path, fuente, nombre) == (False, "url-invalida")
    assert ruta.read_text(encoding="utf-8") == original
    assert not (tmp_path.parent / "escape").exists()


@pytest.mark.parametrize(
    "contenido_bloqueo",
    (
        "{json-invalido",
        "[]",
        '{"version_esquema": 2, "habilidades": {}}',
        (
            '{"version_esquema": 1, "habilidades": {'
            '"../../escape": {"fuente": "git+https://example.com/x.git", '
            '"referencia": "main", "sha_resuelto": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}}'
        ),
        (
            '{"version_esquema": 1, "habilidades": {'
            '"demo": {"fuente": "git+https://example.com/a.git", "referencia": "main", '
            '"sha_resuelto": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}, '
            '"demo": {"fuente": "git+https://example.com/b.git", "referencia": "main", '
            '"sha_resuelto": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}}}'
        ),
    ),
)
def test_lock_completo_invalido_falla_antes_de_aplicar_solo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contenido_bloqueo: str,
) -> None:
    directorio = tmp_path / ".tramalia"
    directorio.mkdir()
    (directorio / "config.json").write_text('{"mode": "team"}', encoding="utf-8")
    (directorio / "habilidades.toml").write_text(
        '[[habilidad]]\nnombre = "demo"\nfuente = "git+https://example.com/demo.git"\n'
        'referencia = "main"\n',
        encoding="utf-8",
    )
    (directorio / "habilidades.lock.json").write_text(contenido_bloqueo, encoding="utf-8")
    llamadas: list[str] = []
    monkeypatch.setattr(
        habilidades,
        "git_disponible",
        lambda: llamadas.append("git") or True,
    )

    with pytest.raises(ErrorConfiguracionHabilidades):
        habilidades.sincronizar_habilidades(tmp_path, solo="demo")

    assert llamadas == []


@pytest.mark.parametrize("modo_git", ("120000", "160000"))
def test_sincronizacion_rechaza_modo_git_antes_del_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    modo_git: str,
) -> None:
    directorio = tmp_path / ".tramalia"
    directorio.mkdir()
    (directorio / "config.json").write_text('{"mode": "local-first"}', encoding="utf-8")
    (directorio / "habilidades.toml").write_text(
        '[[habilidad]]\nnombre = "demo"\nfuente = "git+https://example.com/demo.git"\n'
        'referencia = "main"\n',
        encoding="utf-8",
    )
    sha = "a" * 40
    llamadas: list[tuple[str, ...]] = []

    def ejecutar(argumentos, **_opciones):
        llamada = tuple(argumentos)
        llamadas.append(llamada)
        if "ls-remote" in llamada:
            return ResultadoProceso(llamada, 0, f"{sha}\trefs/heads/main\n", "")
        if "clone" in llamada:
            (Path(llamada[-1]) / ".git").mkdir(parents=True)
            return ResultadoProceso(llamada, 0, "", "")
        if "ls-tree" in llamada:
            return ResultadoProceso(
                llamada,
                0,
                f"{modo_git} blob {sha}\tentrada\n",
                "",
            )
        return ResultadoProceso(llamada, 0, "", "")

    monkeypatch.setattr(habilidades, "git_disponible", lambda: True)
    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)

    resultado = habilidades.sincronizar_habilidades(tmp_path, actualizar=True)

    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == f"modo_git_{modo_git}"
    clon = next(llamada for llamada in llamadas if "clone" in llamada)
    assert "--no-checkout" in clon
    assert "--no-recurse-submodules" in clon
    assert "https://example.com/demo.git" in clon
    assert all("checkout" not in llamada for llamada in llamadas)
    assert not (directorio / "habilidades" / "demo").exists()
    assert not (directorio / ".cuarentena-habilidades").exists()


def test_gitignore_administrado_excluye_cuarentena() -> None:
    assert ".tramalia/.cuarentena-habilidades/" in bloque_gitignore()
