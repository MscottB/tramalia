import types

from tramalia.core import habilidades
from tramalia.core.habilidades import (
    fijar_habilitada,
    leer_habilidades,
    sincronizar_habilidades,
)
from tramalia.core.integraciones import herramientas_relevantes


def test_herramientas_de_arranque_siempre_presentes():
    claves = {herramienta.clave for herramienta in herramientas_relevantes([], ())}
    assert {"mise", "git", "uv"} <= claves


def test_filtrado_por_stack_y_capacidad():
    claves = {herramienta.clave for herramienta in herramientas_relevantes(["node"], ("security",))}
    assert "node" in claves
    assert {"semgrep", "gitleaks"} <= claves
    assert "sqlfluff" not in claves


def test_leer_habilidades_vacio(tmp_path):
    assert leer_habilidades(tmp_path) == ()


def test_leer_habilidades_nuevas(tmp_path):
    (tmp_path / ".tramalia").mkdir()
    (tmp_path / ".tramalia" / "habilidades.toml").write_text(
        '[[habilidad]]\nnombre = "ponytail"\n'
        'fuente = "git+https://example.com/x"\nreferencia = "main"\n',
        encoding="utf-8",
    )

    habilidades = leer_habilidades(tmp_path)

    assert habilidades and habilidades[0].nombre == "ponytail"
    assert habilidades[0].fuente == "git+https://example.com/x"


def test_lector_acepta_manifiesto_heredado_sin_mutarlo(tmp_path):
    (tmp_path / ".tramalia").mkdir()
    ruta_heredada = tmp_path / ".tramalia" / "skills.toml"
    contenido = '[[skill]]\nname = "ponytail"\nsource = "git+https://example.com/x"\nref = "main"\n'
    ruta_heredada.write_text(contenido, encoding="utf-8")

    habilidades = leer_habilidades(tmp_path)

    assert habilidades[0].nombre == "ponytail"
    assert ruta_heredada.read_text(encoding="utf-8") == contenido
    assert not (tmp_path / ".tramalia" / "habilidades.toml").exists()


def test_mutacion_migra_manifiesto_heredado_y_retira_el_antiguo(tmp_path):
    (tmp_path / ".tramalia").mkdir()
    ruta_heredada = tmp_path / ".tramalia" / "skills.toml"
    ruta_heredada.write_text(
        "# comentario conservado\n"
        "[metadata]\n"
        'name = "conservar"\n\n'
        "[[skill]]\n"
        'name = "activa"\nsource = "git+https://example.com/a"\nref = "main"\n\n'
        "# [[skill]]\n"
        '# name = "otra"\n# source = "git+https://example.com/b"\n# ref = "main"\n',
        encoding="utf-8",
    )

    assert fijar_habilitada(tmp_path, "otra", True)

    ruta_nueva = tmp_path / ".tramalia" / "habilidades.toml"
    texto = ruta_nueva.read_text(encoding="utf-8")
    assert not ruta_heredada.exists()
    assert "# comentario conservado" in texto
    assert '[metadata]\nname = "conservar"' in texto
    assert "[[skill]]" not in texto
    assert {habilidad.nombre for habilidad in leer_habilidades(tmp_path)} == {
        "activa",
        "otra",
    }


def test_sincronizar_sin_habilidades_devuelve_estado_explicito(tmp_path):
    resultado = sincronizar_habilidades(tmp_path)
    assert resultado.resoluciones == ()
    assert resultado.estado.estado == "no_disponible"
    assert resultado.estado.motivo == "sin_habilidades_declaradas"


def test_cli_solicitada_devuelve_uno_si_git_no_esta_disponible(tmp_path, monkeypatch) -> None:
    (tmp_path / ".tramalia").mkdir()
    (tmp_path / ".tramalia" / "habilidades.toml").write_text(
        '[[habilidad]]\nnombre = "demo"\n'
        'fuente = "git+https://example.com/demo.git"\nreferencia = "main"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(habilidades, "git_disponible", lambda: False)
    from tramalia.cli import comandos

    argumentos = types.SimpleNamespace(action="sync", name=None)
    assert comandos.comando_habilidades(argumentos) == 1
