"""Manage reproducible project skills backed by immutable Git commits."""

from __future__ import annotations

import json
import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import uuid4

from tramalia.core import procesos
from tramalia.core.modelos import EstadoIntegracion, ValorEstadoIntegracion
from tramalia.core.procesos import ResultadoProceso

_RUTA_MANIFIESTO = Path(".tramalia/habilidades.toml")
_RUTA_MANIFIESTO_HEREDADO = Path(".tramalia/skills.toml")
_RUTA_BLOQUEO = Path(".tramalia/habilidades.lock.json")
_RUTA_HABILIDADES = Path(".tramalia/habilidades")
_SHA_COMPLETO = re.compile(r"[0-9a-fA-F]{40}")
_BLOQUE_NUEVO = re.compile(r"^(#\s*)?\[\[habilidad\]\]\s*$")
_CLAVE_NUEVA = re.compile(r'^(#\s*)?(nombre|fuente|referencia)\s*=\s*"([^"]*)"\s*$')
_BLOQUE_HEREDADO = re.compile(r"^(#\s*)?\[\[skill\]\]\s*$")
_CLAVE_HEREDADA = re.compile(r'^(#\s*)?(name|source|ref)\s*=\s*"([^"]*)"\s*$')
_PROPIA = re.compile(r"^\d{2}-")

_INICIO_GITIGNORE = "# >>> tramalia:skills-externas >>>"
_FIN_GITIGNORE = "# <<< tramalia:skills-externas <<<"
_CUERPO_GITIGNORE = (
    "# Habilidades EXTERNAS: referencias reproducibles, no se suben al repo.\n"
    "# Las habilidades propias NN-* (numeradas) si se versionan.\n"
    ".tramalia/habilidades/*/\n"
    "!.tramalia/habilidades/[0-9][0-9]-*/\n"
)


@dataclass(frozen=True, slots=True)
class HabilidadDeclarada:
    """Describe one external skill declared by a project manifest.

    Attributes:
        nombre: Stable skill name inside the project.
        fuente: Canonical source URL as written in the manifest.
        referencia: Git reference requested by the project.
        habilitada: Whether the manifest block is active.
        instalada: Whether the checkout directory exists locally.
    """

    nombre: str
    fuente: str
    referencia: str
    habilitada: bool
    instalada: bool


@dataclass(frozen=True, slots=True)
class BloqueoHabilidad:
    """Pin a skill source and reference to one immutable Git commit.

    Attributes:
        fuente: Canonical source URL preserved in the lock.
        referencia: Git reference that was resolved.
        sha_resuelto: Verified full commit SHA.
    """

    fuente: str
    referencia: str
    sha_resuelto: str


@dataclass(frozen=True, slots=True)
class ResolucionHabilidad:
    """Report the resolved Git identity and resulting integration state.

    Attributes:
        nombre: Skill name associated with the resolution.
        fuente: Canonical source URL used by the declaration.
        referencia: Requested Git reference.
        sha_resuelto: Verified local SHA, when one remains available.
        accion: Materialization action performed or failed.
        estado: Typed integration state with impact and remediation.
    """

    nombre: str
    fuente: str
    referencia: str
    sha_resuelto: str | None
    accion: Literal["clonada", "rehidratada", "actualizada", "sin_cambios", "fallida"]
    estado: EstadoIntegracion


@dataclass(frozen=True, slots=True)
class ResultadoSincronizacionHabilidades:
    """Aggregate a requested skill synchronization without losing item failures.

    Attributes:
        estado: Aggregate integration state for the request.
        resoluciones: Per-skill resolutions produced by the request.
    """

    estado: EstadoIntegracion
    resoluciones: tuple[ResolucionHabilidad, ...]


def _ruta_manifiesto_lectura(raiz: Path) -> tuple[Path | None, bool]:
    nueva = raiz / _RUTA_MANIFIESTO
    if nueva.exists():
        return nueva, False
    heredada = raiz / _RUTA_MANIFIESTO_HEREDADO
    return (heredada, True) if heredada.exists() else (None, False)


def _datos_manifiesto(ruta: Path, heredado: bool) -> list[dict[str, object]]:
    try:
        datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    entradas = datos.get("skill" if heredado else "habilidad", [])
    return [entrada for entrada in entradas if isinstance(entrada, dict)]


def leer_habilidades(raiz: Path) -> tuple[HabilidadDeclarada, ...]:
    """Read enabled skills from the current or legacy project manifest.

    Args:
        raiz: Project root containing the Tramalia directory.

    Returns:
        Enabled declarations normalized to the Spanish public model.
    """
    ruta, heredado = _ruta_manifiesto_lectura(raiz)
    if ruta is None:
        return ()
    claves = ("name", "source", "ref") if heredado else ("nombre", "fuente", "referencia")
    resultado: list[HabilidadDeclarada] = []
    for entrada in _datos_manifiesto(ruta, heredado):
        nombre = str(entrada.get(claves[0]) or "").strip()
        if not nombre:
            continue
        resultado.append(
            HabilidadDeclarada(
                nombre=nombre,
                fuente=str(entrada.get(claves[1]) or "").strip(),
                referencia=str(entrada.get(claves[2]) or "main").strip() or "main",
                habilitada=True,
                instalada=(raiz / _RUTA_HABILIDADES / nombre).is_dir(),
            )
        )
    return tuple(resultado)


def _catalogo_desde_texto(
    raiz: Path, texto: str, *, heredado: bool
) -> tuple[HabilidadDeclarada, ...]:
    patron_bloque = _BLOQUE_HEREDADO if heredado else _BLOQUE_NUEVO
    patron_clave = _CLAVE_HEREDADA if heredado else _CLAVE_NUEVA
    equivalencias = (
        {"name": "nombre", "source": "fuente", "ref": "referencia"}
        if heredado
        else {"nombre": "nombre", "fuente": "fuente", "referencia": "referencia"}
    )
    lineas = texto.splitlines()
    resultado: list[HabilidadDeclarada] = []
    indice = 0
    while indice < len(lineas):
        bloque = patron_bloque.match(lineas[indice])
        if bloque is None:
            indice += 1
            continue
        valores = {"nombre": "", "fuente": "", "referencia": "main"}
        habilitada = bloque.group(1) is None
        indice += 1
        while indice < len(lineas):
            clave = patron_clave.match(lineas[indice])
            if clave is None:
                break
            valores[equivalencias[clave.group(2)]] = clave.group(3)
            indice += 1
        if valores["nombre"]:
            resultado.append(
                HabilidadDeclarada(
                    nombre=valores["nombre"],
                    fuente=valores["fuente"],
                    referencia=valores["referencia"] or "main",
                    habilitada=habilitada,
                    instalada=(raiz / _RUTA_HABILIDADES / valores["nombre"]).is_dir(),
                )
            )
    return tuple(resultado)


def catalogo_habilidades(raiz: Path) -> tuple[HabilidadDeclarada, ...]:
    """Read enabled and commented skill declarations conservatively.

    Args:
        raiz: Project root containing the Tramalia directory.

    Returns:
        Active and commented declarations in manifest order, or an empty
        tuple when the manifest cannot be read.
    """
    ruta, heredado = _ruta_manifiesto_lectura(raiz)
    if ruta is None:
        return ()
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError:
        return ()
    return _catalogo_desde_texto(raiz, texto, heredado=heredado)


def _validar_manifiesto(ruta: Path) -> None:
    datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    entradas = datos.get("habilidad", [])
    if not isinstance(entradas, list):
        raise ValueError("el manifiesto no contiene una lista de habilidades")


def _publicar_texto_atomico(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(f"{ruta.name}.tmp-{uuid4().hex}")
    try:
        temporal.write_text(texto, encoding="utf-8")
        _validar_manifiesto(temporal)
        temporal.replace(ruta)
    finally:
        temporal.unlink(missing_ok=True)


def _traducir_manifiesto_heredado(texto: str) -> str:
    claves = {"name": "nombre", "source": "fuente", "ref": "referencia"}
    lineas: list[str] = []
    en_bloque_habilidad = False
    for linea in texto.splitlines():
        bloque = re.match(r"^(\s*(?:#\s*)?)\[\[skill\]\](\s*)$", linea)
        if bloque is not None:
            lineas.append(f"{bloque.group(1)}[[habilidad]]{bloque.group(2)}")
            en_bloque_habilidad = True
            continue
        if en_bloque_habilidad:
            clave = re.match(
                r'^(\s*(?:#\s*)?)(name|source|ref)(\s*=\s*"[^"]*"\s*)$',
                linea,
            )
            if clave is not None:
                lineas.append(f"{clave.group(1)}{claves[clave.group(2)]}{clave.group(3)}")
                continue
            en_bloque_habilidad = False
        lineas.append(linea)
    return "\n".join(lineas) + ("\n" if texto.endswith("\n") else "")


def _preparar_manifiesto_escritura(raiz: Path) -> Path | None:
    nueva = raiz / _RUTA_MANIFIESTO
    if nueva.exists():
        return nueva
    heredada = raiz / _RUTA_MANIFIESTO_HEREDADO
    if not heredada.exists():
        return None
    try:
        texto = _traducir_manifiesto_heredado(heredada.read_text(encoding="utf-8"))
        _publicar_texto_atomico(nueva, texto)
        _validar_manifiesto(nueva)
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return None
    heredada.unlink()
    return nueva


def fijar_habilitada(raiz: Path, nombre: str, habilitada: bool) -> bool:
    """Enable or disable one exact manifest block without rewriting others.

    Args:
        raiz: Project root containing the skill manifest.
        nombre: Exact skill name to mutate.
        habilitada: Desired active state for the declaration.

    Returns:
        True when the declaration exists and has the requested state; False
        when no writable declaration can be found.

    Raises:
        OSError: If an existing canonical manifest cannot be read or written.
    """
    ruta = _preparar_manifiesto_escritura(raiz)
    if ruta is None:
        return False
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    indice = 0
    while indice < len(lineas):
        bloque = _BLOQUE_NUEVO.match(lineas[indice])
        if bloque is None:
            indice += 1
            continue
        inicio = indice
        indice += 1
        nombre_bloque: str | None = None
        while indice < len(lineas):
            clave = _CLAVE_NUEVA.match(lineas[indice])
            if clave is None:
                break
            if clave.group(2) == "nombre":
                nombre_bloque = clave.group(3)
            indice += 1
        if nombre_bloque != nombre:
            continue
        actual = bloque.group(1) is None
        if actual == habilitada:
            return True
        for posicion in range(inicio, indice):
            lineas[posicion] = (
                re.sub(r"^#\s?", "", lineas[posicion]) if habilitada else "# " + lineas[posicion]
            )
        _publicar_texto_atomico(ruta, "\n".join(lineas) + "\n")
        return True
    return False


def agregar_habilidad(raiz: Path, fuente: str, nombre: str | None = None) -> tuple[bool, str]:
    """Append one enabled skill using the canonical Spanish manifest format.

    Args:
        raiz: Project root containing the skill manifest.
        fuente: HTTP or ``git+`` source URL to declare.
        nombre: Optional explicit skill name derived from the URL when absent.

    Returns:
        A success flag and either the resolved name or a stable failure reason.

    Raises:
        OSError: If an existing canonical manifest cannot be read or written.
    """
    ruta = _preparar_manifiesto_escritura(raiz)
    if ruta is None:
        return False, "sin-manifiesto"
    fuente_canonica = fuente.strip()
    if not fuente_canonica.startswith(("http://", "https://", "git+")):
        return False, "url-invalida"
    if not fuente_canonica.startswith("git+"):
        fuente_canonica = "git+" + fuente_canonica
    nombre_resuelto = (
        nombre or fuente_canonica.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]
    ).strip()
    if not nombre_resuelto or any(caracter in nombre_resuelto for caracter in ('"', "\r", "\n")):
        return False, "url-invalida"
    if any(habilidad.nombre == nombre_resuelto for habilidad in catalogo_habilidades(raiz)):
        return False, "duplicada"
    texto = ruta.read_text(encoding="utf-8")
    separador = "" if not texto or texto.endswith("\n\n") else "\n"
    bloque = (
        f'{separador}[[habilidad]]\nnombre = "{nombre_resuelto}"\n'
        f'fuente = "{fuente_canonica}"\nreferencia = "main"\n'
    )
    _publicar_texto_atomico(ruta, texto + bloque)
    return True, nombre_resuelto


def habilidades_propias(raiz: Path) -> tuple[dict[str, str], ...]:
    """List numbered project-owned skills and their frontmatter description.

    Args:
        raiz: Project root containing ``.tramalia/habilidades``.

    Returns:
        Skill names and descriptions ordered by directory name.
    """
    base = raiz / _RUTA_HABILIDADES
    if not base.exists():
        return ()
    resultado: list[dict[str, str]] = []
    for directorio in sorted(base.iterdir()):
        archivo = directorio / "SKILL.md"
        if not (directorio.is_dir() and archivo.exists() and _PROPIA.match(directorio.name)):
            continue
        descripcion = ""
        try:
            for linea in archivo.read_text(encoding="utf-8").splitlines()[:6]:
                if linea.startswith("description:"):
                    descripcion = linea.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
        resultado.append({"nombre": directorio.name, "descripcion": descripcion})
    return tuple(resultado)


def bloque_gitignore() -> str:
    """Return the managed ignore block for reproducible external checkouts.

    Returns:
        Complete Tramalia-owned ``.gitignore`` block with a trailing newline.
    """
    return f"{_INICIO_GITIGNORE}\n{_CUERPO_GITIGNORE}{_FIN_GITIGNORE}\n"


def asegurar_gitignore_habilidades(raiz: Path) -> str:
    """Create or update only Tramalia's managed skill ignore block.

    Args:
        raiz: Project root whose ``.gitignore`` must be reconciled.

    Returns:
        ``creado``, ``adaptado``, or ``existe`` according to the mutation.

    Raises:
        OSError: If ``.gitignore`` cannot be read or written.
    """
    ruta = raiz / ".gitignore"
    bloque = bloque_gitignore()
    if not ruta.exists():
        ruta.write_text(bloque, encoding="utf-8")
        return "creado"
    texto = ruta.read_text(encoding="utf-8")
    if _INICIO_GITIGNORE in texto and _FIN_GITIGNORE in texto:
        prefijo = texto[: texto.index(_INICIO_GITIGNORE)]
        sufijo = texto[texto.index(_FIN_GITIGNORE) + len(_FIN_GITIGNORE) :]
        nuevo = prefijo + bloque.rstrip("\n") + sufijo
        if nuevo != texto:
            ruta.write_text(nuevo, encoding="utf-8")
            return "adaptado"
        return "existe"
    separador = "" if texto.endswith("\n\n") else ("\n" if texto.endswith("\n") else "\n\n")
    ruta.write_text(texto + separador + bloque, encoding="utf-8")
    return "adaptado"


def _ejecutar_git(
    argumentos: list[str] | tuple[str, ...],
    *,
    raiz: Path | None = None,
    limite_segundos: float = 120,
) -> ResultadoProceso:
    return procesos.ejecutar(argumentos, raiz=raiz, limite_segundos=limite_segundos)


def habilidades_externas_rastreadas(raiz: Path) -> tuple[str, ...]:
    """List non-numbered external skill directories already tracked by Git.

    Args:
        raiz: Project root inspected through ``git ls-files``.

    Returns:
        Sorted external skill names, or an empty tuple when Git is unavailable
        or the inspection fails.
    """
    if not git_disponible():
        return ()
    resultado = _ejecutar_git(
        ["git", "-C", str(raiz), "ls-files", ".tramalia/habilidades"],
        raiz=raiz,
        limite_segundos=15,
    )
    if not resultado.exitoso:
        return ()
    nombres: set[str] = set()
    for linea in resultado.salida.splitlines():
        partes = linea.strip().replace("\\", "/").split("/")
        if len(partes) >= 3 and partes[:2] == [".tramalia", "habilidades"]:
            if not _PROPIA.match(partes[2]):
                nombres.add(partes[2])
    return tuple(sorted(nombres))


def git_disponible() -> bool:
    """Return whether Git can be resolved on the current process path.

    Returns:
        True when the Git executable can be resolved; otherwise False.
    """
    return procesos.encontrar("git") is not None


def _fuente_para_git(fuente: str) -> str:
    """Return a source URL accepted by the Git executable."""
    # `git+` identifica el transporte en Tramalia, no forma parte de la URL Git.
    return fuente.removeprefix("git+")


def _resolver_sha(fuente: str, referencia: str, raiz: Path) -> tuple[str | None, ResultadoProceso]:
    if referencia == "latest":
        return None, ResultadoProceso(("git", "ls-remote"), 2, "", "latest no permitido")
    resultado = _ejecutar_git(
        [
            "git",
            "ls-remote",
            "--exit-code",
            _fuente_para_git(fuente),
            referencia,
        ],
        raiz=raiz,
        limite_segundos=20,
    )
    if not resultado.exitoso:
        return None, resultado
    primera = resultado.salida.splitlines()[0].split() if resultado.salida.splitlines() else []
    sha = primera[0] if primera else ""
    return (sha if _SHA_COMPLETO.fullmatch(sha) else None), resultado


def _sha_instalado_completo(raiz: Path, nombre: str) -> tuple[str | None, ResultadoProceso]:
    destino = raiz / _RUTA_HABILIDADES / nombre
    resultado = _ejecutar_git(
        ["git", "-C", str(destino), "rev-parse", "HEAD"],
        raiz=raiz,
        limite_segundos=10,
    )
    sha = resultado.salida.strip()
    return (sha if resultado.exitoso and _SHA_COMPLETO.fullmatch(sha) else None), resultado


def referencia_instalada(raiz: Path, nombre: str) -> str | None:
    """Return the seven-character Git identity of an installed external skill.

    Args:
        raiz: Project root containing the external checkout.
        nombre: Exact skill directory name.

    Returns:
        Seven-character commit identity, or None when it cannot be verified.
    """
    destino = raiz / _RUTA_HABILIDADES / nombre / ".git"
    if not destino.exists() or not git_disponible():
        return None
    sha, _resultado = _sha_instalado_completo(raiz, nombre)
    return sha[:7] if sha else None


def _leer_bloqueos(raiz: Path) -> dict[str, BloqueoHabilidad]:
    ruta = raiz / _RUTA_BLOQUEO
    if not ruta.exists():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if datos.get("version_esquema") != 1 or not isinstance(datos.get("habilidades"), dict):
        return {}
    resultado: dict[str, BloqueoHabilidad] = {}
    for nombre, entrada in datos["habilidades"].items():
        if not isinstance(nombre, str) or not isinstance(entrada, dict):
            continue
        fuente = str(entrada.get("fuente") or "")
        referencia = str(entrada.get("referencia") or "")
        sha = str(entrada.get("sha_resuelto") or "")
        if fuente and referencia and _SHA_COMPLETO.fullmatch(sha):
            resultado[nombre] = BloqueoHabilidad(fuente, referencia, sha)
    return resultado


def _publicar_bloqueos(raiz: Path, bloqueos: dict[str, BloqueoHabilidad]) -> None:
    ruta = raiz / _RUTA_BLOQUEO
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {
        "version_esquema": 1,
        "habilidades": {
            nombre: {
                "fuente": bloqueo.fuente,
                "referencia": bloqueo.referencia,
                "sha_resuelto": bloqueo.sha_resuelto,
            }
            for nombre, bloqueo in bloqueos.items()
        },
    }
    temporal = ruta.with_name(f"{ruta.name}.tmp-{uuid4().hex}")
    try:
        temporal.write_text(
            json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        json.loads(temporal.read_text(encoding="utf-8"))
        temporal.replace(ruta)
    finally:
        temporal.unlink(missing_ok=True)


def _estado_habilidad(
    valor: ValorEstadoIntegracion,
    *,
    solicitado: str | None,
    utilizado: str | None,
    motivo: str,
    impacto: str,
    remediacion: str,
) -> EstadoIntegracion:
    return EstadoIntegracion(
        valor,
        "habilidades_git",
        solicitado,
        utilizado,
        motivo,
        impacto,
        remediacion,
    )


def _motivo_fallo_git(resultado: ResultadoProceso, *, resolviendo: bool) -> str:
    if resultado.codigo_salida == 124:
        return "git_tiempo_agotado"
    if resolviendo and resultado.codigo_salida == 2:
        return "referencia_no_resuelta"
    if resultado.codigo_salida != 0:
        return "git_salida_no_cero"
    return "sha_no_verificado"


def _resolucion_fallida(
    habilidad: HabilidadDeclarada,
    resultado: ResultadoProceso,
    *,
    resolviendo: bool = False,
    sha_resuelto: str | None = None,
) -> ResolucionHabilidad:
    motivo = _motivo_fallo_git(resultado, resolviendo=resolviendo)
    return ResolucionHabilidad(
        habilidad.nombre,
        habilidad.fuente,
        habilidad.referencia,
        sha_resuelto,
        "fallida",
        _estado_habilidad(
            ValorEstadoIntegracion.FALLIDO,
            solicitado="git",
            utilizado="git",
            motivo=motivo,
            impacto=(
                "No se pudo verificar la referencia remota; se conserva el SHA local."
                if sha_resuelto is not None
                else "La habilidad no quedo fijada en un commit verificable."
            ),
            remediacion="Corrige la referencia o el acceso Git y vuelve a intentar.",
        ),
    )


def _bloqueo_alineado(habilidad: HabilidadDeclarada, bloqueo: BloqueoHabilidad | None) -> bool:
    return (
        bloqueo is not None
        and bloqueo.fuente == habilidad.fuente
        and bloqueo.referencia == habilidad.referencia
    )


def _resolucion_bloqueo_desalineado(
    habilidad: HabilidadDeclarada, bloqueo: BloqueoHabilidad | None
) -> ResolucionHabilidad:
    return ResolucionHabilidad(
        habilidad.nombre,
        habilidad.fuente,
        habilidad.referencia,
        bloqueo.sha_resuelto if bloqueo is not None else None,
        "fallida",
        _estado_habilidad(
            ValorEstadoIntegracion.FALLIDO,
            solicitado="git",
            utilizado=None,
            motivo="bloqueo_desalineado",
            impacto="El manifiesto no coincide con el bloqueo Team publicado.",
            remediacion="Ejecuta tramalia skills update para mover el bloqueo.",
        ),
    )


def _verificar_checkout(
    raiz: Path, habilidad: HabilidadDeclarada, sha_esperado: str | None = None
) -> tuple[str | None, ResultadoProceso]:
    sha, resultado = _sha_instalado_completo(raiz, habilidad.nombre)
    if sha is not None and sha_esperado is not None and sha.lower() != sha_esperado.lower():
        return None, resultado
    return sha, resultado


def _sincronizar_equipo(
    raiz: Path,
    habilidad: HabilidadDeclarada,
    bloqueo: BloqueoHabilidad | None,
    *,
    actualizar: bool,
) -> tuple[ResolucionHabilidad, BloqueoHabilidad | None]:
    if habilidad.referencia == "latest":
        _sha, resultado = _resolver_sha(habilidad.fuente, habilidad.referencia, raiz)
        return _resolucion_fallida(habilidad, resultado, resolviendo=True), None

    bloqueo_vigente = _bloqueo_alineado(habilidad, bloqueo)
    if not actualizar and (raiz / _RUTA_BLOQUEO).exists() and not bloqueo_vigente:
        return _resolucion_bloqueo_desalineado(habilidad, bloqueo), None
    usa_bloqueo = bloqueo_vigente and not actualizar
    sha_objetivo: str | None
    if usa_bloqueo:
        assert bloqueo is not None
        sha_objetivo = bloqueo.sha_resuelto
    else:
        sha_objetivo, resultado_resolucion = _resolver_sha(
            habilidad.fuente, habilidad.referencia, raiz
        )
        if sha_objetivo is None:
            return (
                _resolucion_fallida(habilidad, resultado_resolucion, resolviendo=True),
                None,
            )
    assert sha_objetivo is not None

    destino = raiz / _RUTA_HABILIDADES / habilidad.nombre
    existia = destino.exists()
    if existia and not (destino / ".git").exists():
        resultado = ResultadoProceso(
            ("git", "checkout"), 1, "", "el destino no es un repositorio Git"
        )
        return _resolucion_fallida(habilidad, resultado), None
    if not existia:
        destino.parent.mkdir(parents=True, exist_ok=True)
        resultado_clon = _ejecutar_git(
            [
                "git",
                "clone",
                "--no-checkout",
                _fuente_para_git(habilidad.fuente),
                str(destino),
            ],
            raiz=raiz,
            limite_segundos=180,
        )
        if not resultado_clon.exitoso:
            if destino.exists():
                shutil.rmtree(destino, ignore_errors=True)
            return _resolucion_fallida(habilidad, resultado_clon), None

    resultado_fetch = _ejecutar_git(
        ["git", "-C", str(destino), "fetch", "origin", sha_objetivo],
        raiz=raiz,
        limite_segundos=120,
    )
    if not resultado_fetch.exitoso:
        if not existia:
            shutil.rmtree(destino, ignore_errors=True)
        return _resolucion_fallida(habilidad, resultado_fetch), None
    resultado_checkout = _ejecutar_git(
        ["git", "-C", str(destino), "checkout", "--detach", sha_objetivo],
        raiz=raiz,
        limite_segundos=120,
    )
    if not resultado_checkout.exitoso:
        if not existia:
            shutil.rmtree(destino, ignore_errors=True)
        return _resolucion_fallida(habilidad, resultado_checkout), None
    sha_verificado, resultado_verificacion = _verificar_checkout(raiz, habilidad, sha_objetivo)
    if sha_verificado is None:
        if not existia:
            shutil.rmtree(destino, ignore_errors=True)
        return _resolucion_fallida(habilidad, resultado_verificacion), None

    accion: Literal["clonada", "rehidratada", "actualizada", "sin_cambios"]
    if not existia:
        accion = "rehidratada" if usa_bloqueo else "clonada"
    elif actualizar:
        accion = "actualizada"
    elif usa_bloqueo:
        accion = "rehidratada"
    else:
        accion = "sin_cambios"
    nuevo_bloqueo = BloqueoHabilidad(habilidad.fuente, habilidad.referencia, sha_verificado)
    return (
        ResolucionHabilidad(
            habilidad.nombre,
            habilidad.fuente,
            habilidad.referencia,
            sha_verificado,
            accion,
            _estado_habilidad(
                ValorEstadoIntegracion.COMPLETO,
                solicitado="git",
                utilizado="git",
                motivo="sha_verificado",
                impacto="sin impacto",
                remediacion="ninguna",
            ),
        ),
        nuevo_bloqueo,
    )


def _sincronizar_local(
    raiz: Path, habilidad: HabilidadDeclarada, *, actualizar: bool
) -> tuple[ResolucionHabilidad, BloqueoHabilidad | None]:
    destino = raiz / _RUTA_HABILIDADES / habilidad.nombre
    existia = destino.exists()
    if existia and not (destino / ".git").exists():
        resultado = ResultadoProceso(
            ("git", "rev-parse"), 1, "", "el destino no es un repositorio Git"
        )
        return _resolucion_fallida(habilidad, resultado), None
    if not existia:
        destino.parent.mkdir(parents=True, exist_ok=True)
        comando = ["git", "clone", "--depth", "1"]
        if habilidad.referencia:
            comando.extend(["--branch", habilidad.referencia])
        comando.extend([_fuente_para_git(habilidad.fuente), str(destino)])
        resultado_clon = _ejecutar_git(comando, raiz=raiz, limite_segundos=180)
        if not resultado_clon.exitoso:
            if destino.exists():
                shutil.rmtree(destino, ignore_errors=True)
            return _resolucion_fallida(habilidad, resultado_clon), None
        accion: Literal["clonada", "actualizada", "sin_cambios"] = "clonada"
    elif actualizar:
        resultado_pull = _ejecutar_git(
            ["git", "-C", str(destino), "pull", "--ff-only"],
            raiz=raiz,
            limite_segundos=120,
        )
        if not resultado_pull.exitoso:
            return _resolucion_fallida(habilidad, resultado_pull), None
        accion = "actualizada"
    else:
        accion = "sin_cambios"

    sha_verificado, resultado_verificacion = _verificar_checkout(raiz, habilidad)
    if sha_verificado is None:
        if not existia:
            shutil.rmtree(destino, ignore_errors=True)
        return _resolucion_fallida(habilidad, resultado_verificacion), None
    bloqueo = BloqueoHabilidad(habilidad.fuente, habilidad.referencia, sha_verificado)
    return (
        ResolucionHabilidad(
            habilidad.nombre,
            habilidad.fuente,
            habilidad.referencia,
            sha_verificado,
            accion,
            _estado_habilidad(
                ValorEstadoIntegracion.COMPLETO,
                solicitado="git",
                utilizado="git",
                motivo="sha_verificado",
                impacto="sin impacto",
                remediacion="ninguna",
            ),
        ),
        bloqueo,
    )


def _estado_agregado(
    resoluciones: tuple[ResolucionHabilidad, ...],
) -> EstadoIntegracion:
    if any(r.estado.estado is ValorEstadoIntegracion.FALLIDO for r in resoluciones):
        valor = ValorEstadoIntegracion.FALLIDO
        motivo = "sincronizacion_fallida"
    elif any(r.estado.estado is ValorEstadoIntegracion.DEGRADADO for r in resoluciones):
        valor = ValorEstadoIntegracion.DEGRADADO
        motivo = "sincronizacion_degradada"
    else:
        valor = ValorEstadoIntegracion.COMPLETO
        motivo = "sincronizacion_completada"
    return _estado_habilidad(
        valor,
        solicitado="git",
        utilizado="git",
        motivo=motivo,
        impacto=(
            "Una o mas habilidades no se sincronizaron."
            if valor is ValorEstadoIntegracion.FALLIDO
            else "sin impacto"
        ),
        remediacion=(
            "Revisa las resoluciones fallidas y repite la operacion."
            if valor is ValorEstadoIntegracion.FALLIDO
            else "ninguna"
        ),
    )


def sincronizar_habilidades(
    raiz: Path,
    solo: str | None = None,
    *,
    actualizar: bool = False,
) -> ResultadoSincronizacionHabilidades:
    """Synchronize declared skills while preserving an immutable Team lock.

    Args:
        raiz: Project root containing the manifest and optional lock.
        solo: Optional exact skill name that limits the request.
        actualizar: Whether moving Team locks to freshly resolved SHAs is
            explicitly authorized.

    Returns:
        Aggregate state and per-skill resolutions. In Team mode, any manifest
        and lock mismatch aborts the complete request before invoking Git.
    """
    habilidades = leer_habilidades(raiz)
    if solo is not None:
        habilidades = tuple(h for h in habilidades if h.nombre == solo)
    if not habilidades:
        return ResultadoSincronizacionHabilidades(
            _estado_habilidad(
                ValorEstadoIntegracion.NO_DISPONIBLE,
                solicitado=None,
                utilizado=None,
                motivo="sin_habilidades_declaradas",
                impacto="No hay habilidades externas que sincronizar.",
                remediacion="Declara una habilidad en el manifiesto si la necesitas.",
            ),
            (),
        )
    from tramalia.core.configuracion import modo_trabajo

    modo = modo_trabajo(raiz)
    bloqueos_originales = _leer_bloqueos(raiz)
    if modo == "team" and not actualizar and (raiz / _RUTA_BLOQUEO).exists():
        desalineadas = tuple(
            _resolucion_bloqueo_desalineado(habilidad, bloqueos_originales.get(habilidad.nombre))
            for habilidad in habilidades
            if not _bloqueo_alineado(habilidad, bloqueos_originales.get(habilidad.nombre))
        )
        if desalineadas:
            return ResultadoSincronizacionHabilidades(_estado_agregado(desalineadas), desalineadas)

    if not git_disponible():
        estado = _estado_habilidad(
            ValorEstadoIntegracion.NO_DISPONIBLE,
            solicitado="git",
            utilizado=None,
            motivo="git_no_instalado",
            impacto="No se pueden materializar las habilidades declaradas.",
            remediacion="Instala Git y repite la operacion.",
        )
        return ResultadoSincronizacionHabilidades(
            estado,
            tuple(
                ResolucionHabilidad(
                    h.nombre,
                    h.fuente,
                    h.referencia,
                    None,
                    "fallida",
                    estado,
                )
                for h in habilidades
            ),
        )

    bloqueos_nuevos = dict(bloqueos_originales)
    resoluciones: list[ResolucionHabilidad] = []
    for habilidad in habilidades:
        if not habilidad.fuente:
            resultado = ResultadoProceso(("git", "clone"), 1, "", "fuente no declarada")
            resolucion, bloqueo = _resolucion_fallida(habilidad, resultado), None
        elif modo == "team":
            resolucion, bloqueo = _sincronizar_equipo(
                raiz,
                habilidad,
                bloqueos_originales.get(habilidad.nombre),
                actualizar=actualizar,
            )
        else:
            resolucion, bloqueo = _sincronizar_local(raiz, habilidad, actualizar=actualizar)
        resoluciones.append(resolucion)
        if bloqueo is not None:
            bloqueos_nuevos[habilidad.nombre] = bloqueo

    resoluciones_finales = tuple(resoluciones)
    estado = _estado_agregado(resoluciones_finales)
    if estado.exitoso and bloqueos_nuevos != bloqueos_originales:
        _publicar_bloqueos(raiz, bloqueos_nuevos)
    return ResultadoSincronizacionHabilidades(estado, resoluciones_finales)


def consultar_habilidades(
    raiz: Path, consultar_remoto: bool = False
) -> tuple[ResolucionHabilidad, ...]:
    """Inspect installed Git identities without mutating skill checkouts.

    Args:
        raiz: Project root containing declared skill checkouts.
        consultar_remoto: Whether each declared reference should be compared
            with ``git ls-remote``.

    Returns:
        One resolution per catalog entry. A failed remote comparison preserves
        the verified local SHA while exposing a failed integration state.
    """
    resoluciones: list[ResolucionHabilidad] = []
    for habilidad in catalogo_habilidades(raiz):
        sha_local, resultado_local = _sha_instalado_completo(raiz, habilidad.nombre)
        if sha_local is None:
            motivo = (
                _motivo_fallo_git(resultado_local, resolviendo=False)
                if habilidad.instalada
                else "habilidad_no_instalada"
            )
            resoluciones.append(
                ResolucionHabilidad(
                    habilidad.nombre,
                    habilidad.fuente,
                    habilidad.referencia,
                    None,
                    "sin_cambios",
                    _estado_habilidad(
                        ValorEstadoIntegracion.NO_DISPONIBLE,
                        solicitado="git",
                        utilizado=None,
                        motivo=motivo,
                        impacto="La habilidad no tiene un SHA local verificable.",
                        remediacion="Sincroniza la habilidad antes de usarla.",
                    ),
                )
            )
            continue
        motivo = "sha_instalado_verificado"
        impacto = "sin impacto"
        if consultar_remoto:
            sha_remoto, resultado_remoto = _resolver_sha(
                habilidad.fuente, habilidad.referencia, raiz
            )
            if sha_remoto is None:
                resoluciones.append(
                    _resolucion_fallida(
                        habilidad,
                        resultado_remoto,
                        resolviendo=True,
                        sha_resuelto=sha_local,
                    )
                )
                continue
            if sha_remoto.lower() != sha_local.lower():
                motivo = "actualizacion_disponible"
                impacto = f"El remoto apunta a {sha_remoto[:7]}."
        resoluciones.append(
            ResolucionHabilidad(
                habilidad.nombre,
                habilidad.fuente,
                habilidad.referencia,
                sha_local,
                "sin_cambios",
                _estado_habilidad(
                    ValorEstadoIntegracion.COMPLETO,
                    solicitado="git",
                    utilizado="git",
                    motivo=motivo,
                    impacto=impacto,
                    remediacion=(
                        "Ejecuta tramalia skills update para mover el bloqueo."
                        if motivo == "actualizacion_disponible"
                        else "ninguna"
                    ),
                ),
            )
        )
    return tuple(resoluciones)
