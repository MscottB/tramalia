from pathlib import Path

import pytest

from tramalia.core import contexto
from tramalia.core.contexto import construir_contexto
from tramalia.core.procesos import ResultadoProceso


def test_contexto_genera_archivos_derivados_con_fallback_stdlib(tmp_path, monkeypatch):
    monkeypatch.setattr(contexto.procesos, "encontrar", lambda _comando: None)
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    resultado = construir_contexto(tmp_path)
    nombres = {ruta.name for ruta in resultado.archivos}

    assert nombres == {"tech-stack.md", "project-map.md"}
    contexto_generado = tmp_path / ".tramalia" / "context"
    assert (contexto_generado / "tech-stack.md").exists()
    assert (contexto_generado / "project-map.md").exists()
    assert resultado.integracion.estado == "degradado"
    assert resultado.integracion.solicitado == "repomix"
    assert resultado.integracion.utilizado == "arbol_stdlib"
    assert resultado.integracion.motivo == "alternativa_completada"


def test_contexto_anuncia_repomix_solo_despues_de_completarlo(tmp_path, monkeypatch):
    monkeypatch.setattr(contexto.procesos, "encontrar", lambda _comando: "repomix")

    def ejecutar(argumentos, **_opciones):
        ruta_salida = Path(argumentos[-1])
        ruta_salida.write_text("snapshot\n", encoding="utf-8")
        return ResultadoProceso(tuple(argumentos), 0, "", "")

    monkeypatch.setattr(contexto.procesos, "ejecutar", ejecutar)

    resultado = construir_contexto(tmp_path)

    assert {ruta.name for ruta in resultado.archivos} == {
        "tech-stack.md",
        "project-map.md",
        "repomix-output.md",
    }
    assert resultado.integracion.estado == "completo"
    assert resultado.integracion.utilizado == "repomix"


@pytest.mark.parametrize(
    ("codigo_salida", "agotado_tiempo"),
    [(124, True), (127, False), (7, False)],
)
def test_contexto_no_anuncia_repomix_si_el_proceso_falla(
    tmp_path, monkeypatch, codigo_salida, agotado_tiempo
):
    ruta_repomix = tmp_path / ".tramalia" / "context" / "repomix-output.md"
    ruta_repomix.parent.mkdir(parents=True)
    ruta_repomix.write_text("salida obsoleta o parcial\n", encoding="utf-8")
    monkeypatch.setattr(contexto.procesos, "encontrar", lambda _comando: "repomix")
    monkeypatch.setattr(
        contexto.procesos,
        "ejecutar",
        lambda *argumentos, **opciones: ResultadoProceso(
            ("repomix",),
            codigo_salida,
            "",
            "fallo simulado",
            agotado_tiempo=agotado_tiempo,
        ),
    )

    resultado = construir_contexto(tmp_path)

    assert "repomix-output.md" not in {ruta.name for ruta in resultado.archivos}
    assert not ruta_repomix.exists()
    assert {ruta.name for ruta in resultado.archivos} == {
        "tech-stack.md",
        "project-map.md",
    }
    assert resultado.integracion.estado == "fallido"
