from tramalia.core import context as contexto
from tramalia.core.context import build_context
from tramalia.core.procesos import ResultadoProceso


def test_context_generates_derived_files(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    results = build_context(tmp_path)
    assert "tech-stack.md" in results
    assert "project-map.md" in results
    ctx = tmp_path / ".tramalia" / "context"
    assert (ctx / "tech-stack.md").exists()
    assert (ctx / "project-map.md").exists()


def test_contexto_no_anuncia_repomix_si_el_proceso_falla(tmp_path, monkeypatch):
    monkeypatch.setattr(contexto.procesos, "encontrar", lambda _comando: "repomix")
    monkeypatch.setattr(
        contexto.procesos,
        "ejecutar",
        lambda *argumentos, **opciones: ResultadoProceso(
            ("repomix",),
            124,
            "",
            "tiempo agotado",
            agotado_tiempo=True,
        ),
    )

    resultados = build_context(tmp_path)

    assert "repomix-output.md" not in resultados
    assert not (tmp_path / ".tramalia" / "context" / "repomix-output.md").exists()
