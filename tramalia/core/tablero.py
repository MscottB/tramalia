"""Provide immutable dashboard snapshots and shared operations for Textual."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from tramalia.core import doctor, installer
from tramalia.core.configuracion import (
    agentes_predeterminados,
    descripcion_tarea,
    fijar_proveedor_contexto,
    fijar_version_andamiaje,
    id_tarea_actual,
    proveedor_contexto,
)
from tramalia.core.detect import detect_stack, enabled_features
from tramalia.core.errores import ErrorTramalia
from tramalia.core.evidencia import leer_bitacora
from tramalia.core.habilidades import (
    ResolucionHabilidad,
    ResultadoSincronizacionHabilidades,
    agregar_habilidad,
    consultar_habilidades,
    fijar_habilitada,
    habilidades_externas_rastreadas,
    habilidades_propias,
    sincronizar_habilidades,
)
from tramalia.core.integraciones import Herramienta, detectar_agentes_predeterminados
from tramalia.core.modelos import (
    EntradaBitacora,
    EstadoIntegracion,
    EstadoProyecto,
    ExcepcionFallo,
    ResultadoCierre,
    ValorEstadoIntegracion,
)
from tramalia.core.operaciones import cerrar_proyecto
from tramalia.core.proveedor_contexto import PROVEEDORES, proveedor_disponible
from tramalia.core.proyecto import inspeccionar_estado_proyecto
from tramalia.core.puertas_calidad import cargar_puertas
from tramalia.core.scaffold import scaffold


@dataclass(frozen=True, slots=True)
class HerramientaTablero:
    """Represent one immutable tool row in the terminal dashboard."""

    comando: str
    proposito: str
    estado: str
    detalle: str
    categoria: str = ""
    presente: bool = False
    opciones_instalacion: tuple[installer.InstallOption, ...] = ()
    herramienta: Herramienta | None = None


@dataclass(frozen=True, slots=True)
class HabilidadPropiaTablero:
    """Represent one project-owned skill without exposing mutable mappings."""

    nombre: str
    descripcion: str


@dataclass(frozen=True, slots=True)
class ProveedorTablero:
    """Represent one context provider and its probed availability."""

    nombre: str
    etiqueta: str
    alcance: str
    ideal: str
    disponible: bool


@dataclass(frozen=True, slots=True)
class DetalleBitacoraTablero:
    """Store preloaded audit detail so selection never touches the filesystem."""

    id_paquete: str
    texto: str


@dataclass(frozen=True, slots=True)
class InstantaneaTablero:
    """Contain all immutable data needed to render one dashboard frame."""

    raiz: Path
    proyecto: EstadoProyecto
    tecnologias: tuple[str, ...]
    puertas: tuple[str, ...]
    herramientas: tuple[HerramientaTablero, ...]
    habilidades: tuple[ResolucionHabilidad, ...]
    bitacora: tuple[EntradaBitacora, ...]
    integraciones: tuple[EstadoIntegracion, ...]
    id_tarea: str | None
    agente: str
    revisor: str
    proveedor_contexto: str
    uv_en_ruta: bool = True
    habilidades_propias: tuple[HabilidadPropiaTablero, ...] = ()
    habilidades_rastreadas: tuple[str, ...] = ()
    proveedores: tuple[ProveedorTablero, ...] = ()
    detalles_bitacora: tuple[DetalleBitacoraTablero, ...] = ()
    descripcion_tarea: str | None = None

    @classmethod
    def vacia(cls, raiz: Path, proyecto: EstadoProyecto) -> InstantaneaTablero:
        """Create a renderable snapshot when no optional data is available."""
        return cls(raiz, proyecto, (), (), (), (), (), (), None, "", "", "serena")


class ServicioTablero:
    """Obtain dashboard snapshots and execute shared core operations."""

    def __init__(
        self,
        raiz: Path,
        *,
        operacion_cerrar: Callable[..., ResultadoCierre] = cerrar_proyecto,
    ) -> None:
        self.raiz = raiz
        self._operacion_cerrar = operacion_cerrar

    def obtener_instantanea(self) -> InstantaneaTablero:
        """Collect one immutable view of project and integration state."""
        proyecto = inspeccionar_estado_proyecto(self.raiz)
        reporte = doctor.diagnose(self.raiz)
        agente, revisor = agentes_predeterminados(self.raiz)
        integraciones: list[EstadoIntegracion] = []
        try:
            puertas = tuple(puerta.nombre for puerta in cargar_puertas(self.raiz))
        except ErrorTramalia as error_dominio:
            puertas = ()
            integraciones.append(
                EstadoIntegracion(
                    ValorEstadoIntegracion.FALLIDO,
                    "puertas_calidad",
                    "mise",
                    "mise",
                    error_dominio.codigo,
                    "no se puede cerrar",
                    error_dominio.sugerencia,
                )
            )
        herramientas: list[HerramientaTablero] = []
        for estado in reporte.statuses:
            opciones = (
                tuple(installer.options_for(estado.herramienta)) if not estado.presente else ()
            )
            mejor = next((opcion for opcion in opciones if opcion.available), None)
            detalle = estado.version or (
                mejor.display
                if mejor is not None
                else opciones[0].display
                if opciones
                else estado.herramienta.sugerencia_instalacion
            )
            herramientas.append(
                HerramientaTablero(
                    estado.herramienta.comando,
                    estado.herramienta.rol,
                    "completo" if estado.presente else "no_disponible",
                    detalle,
                    estado.herramienta.categoria,
                    estado.presente,
                    opciones,
                    estado.herramienta,
                )
            )
        habilidades_proyecto = tuple(
            HabilidadPropiaTablero(
                entrada.get("nombre", ""),
                entrada.get("descripcion", ""),
            )
            for entrada in habilidades_propias(self.raiz)
        )
        proveedores = tuple(
            ProveedorTablero(
                nombre,
                metadatos["etiqueta"],
                metadatos["alcance"],
                metadatos["ideal"],
                proveedor_disponible(nombre),
            )
            for nombre, metadatos in PROVEEDORES.items()
        )
        bitacora = tuple(leer_bitacora(self.raiz))
        detalles_bitacora: list[DetalleBitacoraTablero] = []
        for entrada in bitacora:
            if entrada.error:
                texto = entrada.error
            else:
                ruta_metadatos = entrada.ruta / "metadatos.json"
                try:
                    texto = ruta_metadatos.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    texto = ""
            detalles_bitacora.append(DetalleBitacoraTablero(entrada.id_paquete, texto))
        tarea = id_tarea_actual(self.raiz)
        return InstantaneaTablero(
            raiz=self.raiz,
            proyecto=proyecto,
            tecnologias=tuple(reporte.stack),
            puertas=puertas,
            herramientas=tuple(herramientas),
            habilidades=consultar_habilidades(self.raiz),
            bitacora=bitacora,
            integraciones=tuple(integraciones),
            id_tarea=tarea,
            agente=agente,
            revisor=revisor,
            proveedor_contexto=proveedor_contexto(self.raiz),
            uv_en_ruta=reporte.uv_bin_on_path,
            habilidades_propias=habilidades_proyecto,
            habilidades_rastreadas=habilidades_externas_rastreadas(self.raiz),
            proveedores=proveedores,
            detalles_bitacora=tuple(detalles_bitacora),
            descripcion_tarea=descripcion_tarea(self.raiz, tarea) if tarea else None,
        )

    def cerrar(
        self,
        id_tarea: str,
        *,
        agente: str = "",
        revisor: str = "",
        modelo: str = "",
        excepciones: Sequence[ExcepcionFallo] = (),
    ) -> ResultadoCierre:
        """Delegate closure without reinterpreting its domain result."""
        return self._operacion_cerrar(
            self.raiz,
            id_tarea,
            agente=agente,
            revisor=revisor,
            modelo=modelo,
            excepciones=excepciones,
        )

    def sincronizar_habilidades(
        self,
        solo: str | None = None,
        *,
        actualizar: bool = False,
    ) -> ResultadoSincronizacionHabilidades:
        """Synchronize declared skills through the shared core service."""
        return sincronizar_habilidades(self.raiz, solo, actualizar=actualizar)

    def consultar_actualizaciones(self) -> tuple[ResolucionHabilidad, ...]:
        """Inspect remote skill references without mutating local checkouts."""
        return consultar_habilidades(self.raiz, consultar_remoto=True)

    def agregar_habilidad(self, fuente: str) -> tuple[bool, str]:
        """Declare one external skill through the shared manifest API."""
        return agregar_habilidad(self.raiz, fuente)

    def habilitar_y_sincronizar(
        self,
        nombre: str,
        *,
        habilitar: bool,
        actualizar: bool,
    ) -> ResultadoSincronizacionHabilidades:
        """Enable a selected skill when needed and synchronize only that skill."""
        if habilitar:
            fijar_habilitada(self.raiz, nombre, True)
        return sincronizar_habilidades(self.raiz, nombre, actualizar=actualizar)

    def describir_tarea(self, id_tarea: str) -> str | None:
        """Read one task description for an asynchronous form refresh."""
        return descripcion_tarea(self.raiz, id_tarea)

    def fijar_proveedor(self, nombre: str) -> tuple[bool, bool]:
        """Persist a context provider and report whether it is available."""
        guardado = fijar_proveedor_contexto(self.raiz, nombre)
        return guardado, proveedor_disponible(nombre) if guardado else False

    def inicializar(self, version: str) -> None:
        """Scaffold the current root using detected defaults in a worker thread."""
        tecnologias = detect_stack(self.raiz)
        agente, revisor = detectar_agentes_predeterminados()
        scaffold(
            self.raiz,
            {
                "project_name": self.raiz.name,
                "stacks": tecnologias,
                "features": enabled_features(tecnologias),
                "primary_agent": agente,
                "reviewer_agent": revisor,
            },
        )
        fijar_version_andamiaje(self.raiz, version)
