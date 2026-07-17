import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from tramalia.core import seguridad_entradas
from tramalia.core.errores import ErrorEntradaInsegura
from tramalia.core.procesos import ResultadoProceso
from tramalia.core.seguridad_entradas import (
    ResumenArbolHabilidad,
    leer_texto_confinado,
    resolver_ruta_confinada,
    sanear_texto_externo,
    validar_arbol_habilidad,
    validar_fuente_git,
    validar_nombre_habilidad,
)

pytestmark = pytest.mark.unidad


@pytest.mark.parametrize(
    "nombre",
    ("../escape", "..\\escape", "/tmp/x", "C:\\x", "CON", "a/b", "a\\b", ""),
)
def test_nombre_habilidad_rechaza_rutas_y_dispositivos(nombre: str) -> None:
    with pytest.raises(ErrorEntradaInsegura, match="nombre de habilidad"):
        validar_nombre_habilidad(nombre)


@pytest.mark.parametrize(
    "fuente",
    ("http://example.com/x.git", "git+http://example.com/x.git", "file:///tmp/x", "ssh://host/x"),
)
def test_fuente_habilidad_exige_https(fuente: str) -> None:
    with pytest.raises(ErrorEntradaInsegura, match="HTTPS"):
        validar_fuente_git(fuente)


def test_fuente_https_se_normaliza() -> None:
    assert validar_fuente_git("https://example.com/x.git") == "git+https://example.com/x.git"


def test_fuente_malformada_falla_con_error_tipado_sin_filtrar_valor() -> None:
    fuente = "https://[::1"

    with pytest.raises(ErrorEntradaInsegura) as captura:
        validar_fuente_git(fuente)

    assert fuente not in str(captura.value)


@pytest.mark.parametrize(
    "fuente",
    (
        "https://usuario:clave@example.invalid/x.git",
        "https://example.invalid/x.git?seleccion=uno",
        "https://example.invalid/x.git#revision",
        "https://example.invalid/\nx.git",
        "https://example.invalid/\tx.git",
        "https://example.invalid/x y.git",
    ),
    ids=("credenciales", "query", "fragmento", "salto", "tab", "espacio"),
)
def test_fuente_https_rechaza_componentes_que_pueden_persistir_datos(fuente: str) -> None:
    with pytest.raises(ErrorEntradaInsegura) as captura:
        validar_fuente_git(fuente)

    assert fuente not in str(captura.value)


@pytest.mark.parametrize(
    ("fuente", "esperada"),
    (
        ("https://example.invalid/x.git", "git+https://example.invalid/x.git"),
        ("git+https://example.invalid/x.git", "git+https://example.invalid/x.git"),
        ("https://[2001:db8::1]/x.git", "git+https://[2001:db8::1]/x.git"),
    ),
    ids=("https", "git-https", "ipv6"),
)
def test_fuente_https_con_forma_legitima_se_conserva(fuente: str, esperada: str) -> None:
    assert validar_fuente_git(fuente) == esperada


def test_nombre_habilidad_valido_se_conserva() -> None:
    assert validar_nombre_habilidad("habilidad-1.0") == "habilidad-1.0"


@pytest.mark.parametrize("nombre", ("A", ".inicio", "fin-", "a" * 65, "COM9", "lpt1"))
def test_nombre_habilidad_aplica_patron_portable_exacto(nombre: str) -> None:
    with pytest.raises(ErrorEntradaInsegura):
        validar_nombre_habilidad(nombre)


def test_nombre_habilidad_acepta_limites_del_patron() -> None:
    assert validar_nombre_habilidad("a") == "a"
    assert validar_nombre_habilidad("a" + "_" * 62 + "z") == "a" + "_" * 62 + "z"


def test_resolver_ruta_confinada_rechaza_traversal_y_absoluta(tmp_path: Path) -> None:
    raiz = tmp_path / "proyecto"
    raiz.mkdir()

    with pytest.raises(ErrorEntradaInsegura, match="ruta"):
        resolver_ruta_confinada(raiz, Path("../secreto.txt"), permitir_ausente=True)
    with pytest.raises(ErrorEntradaInsegura, match="ruta"):
        resolver_ruta_confinada(raiz, (tmp_path / "secreto.txt").resolve(), permitir_ausente=True)


def test_resolver_ruta_confinada_controla_ausencia(tmp_path: Path) -> None:
    raiz = tmp_path / "proyecto"
    raiz.mkdir()
    relativa = Path("docs/archivo.txt")

    with pytest.raises(ErrorEntradaInsegura, match="no existe"):
        resolver_ruta_confinada(raiz, relativa)

    assert (
        resolver_ruta_confinada(raiz, relativa, permitir_ausente=True)
        == (raiz / relativa).resolve()
    )


def _crear_symlink_o_saltar(enlace: Path, destino: Path, *, directorio: bool) -> None:
    try:
        enlace.symlink_to(destino, target_is_directory=directorio)
    except OSError as error_symlink:
        pytest.skip(f"El entorno no permite symlinks: {error_symlink}")


def test_resolver_ruta_confinada_rechaza_symlink_fuera_de_raiz(tmp_path: Path) -> None:
    raiz = tmp_path / "proyecto"
    raiz.mkdir()
    secreto = tmp_path / "secreto.txt"
    secreto.write_text("secreto", encoding="utf-8")
    enlace = raiz / "AGENTS.md"
    _crear_symlink_o_saltar(enlace, secreto, directorio=False)

    with pytest.raises(ErrorEntradaInsegura, match="fuera"):
        resolver_ruta_confinada(raiz, Path("AGENTS.md"))


@pytest.mark.parametrize("es_directorio", (False, True))
def test_arbol_habilidad_rechaza_symlink_de_archivo_o_directorio(
    tmp_path: Path,
    es_directorio: bool,
) -> None:
    raiz = tmp_path / "habilidad"
    raiz.mkdir()
    destino = tmp_path / ("destino" if es_directorio else "destino.txt")
    if es_directorio:
        destino.mkdir()
    else:
        destino.write_text("dato", encoding="utf-8")
    _crear_symlink_o_saltar(raiz / "enlace", destino, directorio=es_directorio)

    with pytest.raises(ErrorEntradaInsegura, match="enlace"):
        validar_arbol_habilidad(raiz)


def test_arbol_habilidad_rechaza_reparse_point_simulado(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raiz = tmp_path / "habilidad"
    raiz.mkdir()
    archivo = raiz / "SKILL.md"
    archivo.write_text("contenido", encoding="utf-8")
    lstat_real = Path.lstat

    def lstat_simulado(ruta: Path):
        resultado = lstat_real(ruta)
        if ruta == archivo:
            return SimpleNamespace(
                st_mode=resultado.st_mode,
                st_size=resultado.st_size,
                st_file_attributes=getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
            )
        return resultado

    monkeypatch.setattr(Path, "lstat", lstat_simulado)

    with pytest.raises(ErrorEntradaInsegura, match="reparse"):
        validar_arbol_habilidad(raiz)


def test_arbol_habilidad_rechaza_gitmodules(tmp_path: Path) -> None:
    raiz = tmp_path / "habilidad"
    raiz.mkdir()
    (raiz / ".gitmodules").write_text("[submodule]", encoding="utf-8")

    with pytest.raises(ErrorEntradaInsegura, match=".gitmodules"):
        validar_arbol_habilidad(raiz)


def test_arbol_habilidad_no_cuenta_directorio_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raiz = tmp_path / "habilidad"
    (raiz / ".git" / "objetos").mkdir(parents=True)
    for indice in range(2_001):
        (raiz / ".git" / "objetos" / str(indice)).touch()
    (raiz / "SKILL.md").write_bytes(b"abc")
    monkeypatch.setattr(
        seguridad_entradas,
        "procesos",
        SimpleNamespace(
            ejecutar=lambda *_argumentos, **_opciones: ResultadoProceso(
                ("git", "ls-tree"), 0, "", ""
            )
        ),
        raising=False,
    )

    assert validar_arbol_habilidad(raiz) == ResumenArbolHabilidad(
        archivos=1,
        bytes_totales=3,
    )


@pytest.mark.parametrize("modo", ("120000", "160000"))
def test_arbol_habilidad_rechaza_modos_git_inseguros(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    modo: str,
) -> None:
    raiz = tmp_path / "habilidad"
    (raiz / ".git").mkdir(parents=True)
    (raiz / "SKILL.md").write_text("contenido", encoding="utf-8")
    salida = f"{modo} blob {'a' * 40}\tentrada-insegura\n"
    monkeypatch.setattr(
        seguridad_entradas,
        "procesos",
        SimpleNamespace(
            ejecutar=lambda *_argumentos, **_opciones: ResultadoProceso(
                ("git", "ls-tree"),
                0,
                salida,
                "",
            )
        ),
        raising=False,
    )

    with pytest.raises(ErrorEntradaInsegura, match=modo):
        validar_arbol_habilidad(raiz)


def test_arbol_habilidad_rechaza_mas_de_dos_mil_archivos(tmp_path: Path) -> None:
    raiz = tmp_path / "habilidad"
    raiz.mkdir()
    for indice in range(2_001):
        (raiz / f"archivo-{indice}").touch()

    with pytest.raises(ErrorEntradaInsegura, match="2.000"):
        validar_arbol_habilidad(raiz)


def test_arbol_habilidad_rechaza_archivo_mayor_de_cuatro_mib(tmp_path: Path) -> None:
    raiz = tmp_path / "habilidad"
    raiz.mkdir()
    with (raiz / "grande.bin").open("wb") as archivo:
        archivo.truncate(4 * 1024 * 1024 + 1)

    with pytest.raises(ErrorEntradaInsegura, match="4 MiB"):
        validar_arbol_habilidad(raiz)


def test_arbol_habilidad_rechaza_total_mayor_de_sesenta_y_cuatro_mib(
    tmp_path: Path,
) -> None:
    raiz = tmp_path / "habilidad"
    raiz.mkdir()
    for indice in range(16):
        with (raiz / f"bloque-{indice}.bin").open("wb") as archivo:
            archivo.truncate(4 * 1024 * 1024)
    (raiz / "exceso.bin").write_bytes(b"x")

    with pytest.raises(ErrorEntradaInsegura, match="64 MiB"):
        validar_arbol_habilidad(raiz)


def test_saneamiento_elimina_ansi_osc_nul_y_controles_c0() -> None:
    entrada = "\x1b[31mrojo\x1b[0m\x1b]0;titulo-secreto\x07texto\x00\x01\n\tfin"

    salida = sanear_texto_externo(entrada)

    assert "rojo" in salida
    assert "texto" in salida
    assert "\n\tfin" in salida
    assert "\x1b" not in salida
    assert "titulo-secreto" not in salida
    assert "\x00" not in salida
    assert "\x01" not in salida


@pytest.mark.parametrize(
    "asignacion",
    (
        "token=valor-real",
        "mi_secret: valor-real",
        "PASSWORD = valor-real",
        "contrasena=valor-real",
        "prefijo_api_key_sufijo: valor-real",
        "X-API-Key: valor-real",
        "authorization=valor-real",
    ),
)
def test_saneamiento_redacta_asignaciones_secretas(asignacion: str) -> None:
    salida = sanear_texto_externo(asignacion)

    assert "valor-real" not in salida
    assert "[REDACTADO]" in salida


def test_saneamiento_conserva_asignacion_con_guiones_no_sensible() -> None:
    entrada = "X-Request-Id: valor-publico"

    assert sanear_texto_externo(entrada) == entrada


def test_saneamiento_limita_linea_en_bytes_sin_cortar_utf8() -> None:
    salida = sanear_texto_externo("a" * 10_000 + "á" * 6_000)
    contenido, marca = salida.split("\n", 1)

    assert len(contenido.encode("utf-8")) <= 8_192
    assert "�" not in salida
    assert marca.startswith("[TRUNCADO: ")


def test_saneamiento_limita_total_en_bytes_incluyendo_marca() -> None:
    salida = sanear_texto_externo(("x" * 1_000 + "\n") * 200)

    assert len(salida.encode("utf-8")) <= 131_072
    assert "[TRUNCADO: " in salida


def test_saneamiento_no_invoca_repr_ni_str_arbitrarios() -> None:
    class ObjetoHostil:
        def __repr__(self) -> str:
            raise AssertionError("repr no debe invocarse")

        def __str__(self) -> str:
            raise AssertionError("str no debe invocarse")

    salida = sanear_texto_externo(ObjetoHostil())

    assert salida.startswith("<objeto_no_serializable:")
    assert "ObjetoHostil" in salida


def test_saneamiento_no_invoca_str_de_subclases_escalares() -> None:
    llamadas: list[str] = []

    class EnteroHostil(int):
        def __str__(self) -> str:
            llamadas.append("entero")
            raise AssertionError("str no debe invocarse")

    class FlotanteHostil(float):
        def __str__(self) -> str:
            llamadas.append("flotante")
            raise AssertionError("str no debe invocarse")

    salida_entero = sanear_texto_externo(EnteroHostil(7))
    salida_flotante = sanear_texto_externo(FlotanteHostil(2.5))

    assert llamadas == []
    assert "EnteroHostil" in salida_entero
    assert "FlotanteHostil" in salida_flotante


@pytest.mark.parametrize(
    ("valor", "esperada"),
    ((True, "true"), (False, "false"), (7, "7"), (2.5, "2.5")),
)
def test_saneamiento_conserva_escalares_incorporados_exactos(
    valor: bool | int | float,
    esperada: str,
) -> None:
    assert sanear_texto_externo(valor) == esperada


def test_leer_texto_confinado_limita_archivo_grande_en_bytes(tmp_path: Path) -> None:
    raiz = tmp_path / "proyecto"
    raiz.mkdir()
    (raiz / "AGENTS.md").write_text("x" * 200_000, encoding="utf-8")

    salida = leer_texto_confinado(raiz, Path("AGENTS.md"))

    assert len(salida.encode("utf-8")) <= 131_072
    assert "[TRUNCADO: " in salida
