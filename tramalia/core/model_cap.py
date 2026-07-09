"""Tope (cap) de modelos para los subagentes, portable entre proveedores.

Claude Code rutea por rol de forma nativa (el `model:` de cada .claude/agents/*.md);
Tramalia puede aplicar un TOPE opcional: ningún rol usa un modelo por encima del
tope elegido. "Sonnet hacia abajo" = tope sonnet → opus/fable bajan a sonnet,
haiku se conserva, ejecutor (inherit) no se toca.

Ranking de capacidad (mayor → menor): fable > opus > sonnet > haiku.

En hosts SIN ruteo por rol (Codex, Antigravity, gateways) no hay enforcement
posible sin configurar la máquina del usuario (frontera de Gentle-AI): el tope
viaja como REGLA en AGENTS.md + `model_cap` en tools.json, y aquí se generan las
EQUIVALENCIAS por nivel de capacidad (no por nombre de modelo, que cambia seguido)
para que el usuario/Gentle-AI las apliquen.
"""

from __future__ import annotations

import re
from pathlib import Path

# ranking de capacidad para el `model:` de Claude Code (mayor número = más capaz)
_RANK = {"fable": 4, "opus": 3, "sonnet": 2, "haiku": 1}
CAPS = ("fable", "opus", "sonnet", "haiku")  # valores de tope válidos (+ "none")

# modelo por rol de los 5 subagentes que genera `init` (la base sobre la que se capa)
ROLE_DEFAULTS: dict[str, str] = {
    "planificador": "opus",
    "ejecutor": "inherit",
    "revisor": "opus",
    "documentador": "haiku",
    "resolutor-profundo": "fable",
}

# nivel de capacidad legible + equivalencia por proveedor (host sin ruteo nativo).
# Se evita nombrar modelos concretos de terceros: se usa la CAPACIDAD.
LEVELS: dict[str, dict[str, str]] = {
    "fable":  {"level": "profundo (deep)",
               "codex": "perfil de razonamiento profundo (model_reasoning_effort = high)",
               "antigravity": "modelo de razonamiento máximo"},
    "opus":   {"level": "alto (high)",
               "codex": "model_reasoning_effort = high",
               "antigravity": "modelo Pro / de alta capacidad"},
    "sonnet": {"level": "estándar (standard)",
               "codex": "perfil estándar (model_reasoning_effort = medium)",
               "antigravity": "modelo estándar (no el de razonamiento profundo)"},
    "haiku":  {"level": "ligero (light)",
               "codex": "modelo rápido / model_reasoning_effort = low",
               "antigravity": "modelo Flash / rápido"},
}


def cap_model(model: str, cap: str) -> str:
    """Aplica el tope a un modelo. Si lo supera, lo baja al tope; si no, lo conserva.
    `inherit` y valores fuera del ranking no se tocan."""
    if not cap or cap == "none" or model not in _RANK or cap not in _RANK:
        return model
    return cap if _RANK[model] > _RANK[cap] else model


def resolved_models(cap: str) -> dict[str, str]:
    """El modelo resultante por rol tras aplicar `cap` sobre ROLE_DEFAULTS."""
    return {role: cap_model(default, cap) for role, default in ROLE_DEFAULTS.items()}


def apply_to_agents(root: Path, cap: str) -> list[tuple[str, str]]:
    """Reescribe SOLO la línea `model:` de cada .claude/agents/<rol>.md según
    ROLE_DEFAULTS capado a `cap` (o los defaults si cap es none). Conservador:
    no toca el cuerpo del agente. Devuelve [(rol, modelo_resultante)]."""
    base = root / ".claude" / "agents"
    out: list[tuple[str, str]] = []
    objetivos = resolved_models(cap)
    for role, target in objetivos.items():
        f = base / f"{role}.md"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        new = re.sub(r"(?m)^model:\s*.+$", f"model: {target}", text, count=1)
        if new != text:
            f.write_text(new, encoding="utf-8")
        out.append((role, target))
    return out


def current_agent_models(root: Path) -> dict[str, str]:
    """Lee el `model:` actual de cada .claude/agents/<rol>.md (lo que hay en disco)."""
    base = root / ".claude" / "agents"
    out: dict[str, str] = {}
    for role in ROLE_DEFAULTS:
        f = base / f"{role}.md"
        if not f.exists():
            continue
        m = re.search(r"(?m)^model:\s*(.+)$", f.read_text(encoding="utf-8"))
        out[role] = m.group(1).strip() if m else "?"
    return out


def equivalence_lines(cap: str) -> list[str]:
    """Equivalencia del tope por proveedor (para copiar; Tramalia no la escribe)."""
    if not cap or cap == "none" or cap not in LEVELS:
        return []
    lvl = LEVELS[cap]
    return [
        f"nivel de capacidad: {lvl['level']}",
        f"  Codex (~/.codex/config.toml): {lvl['codex']}",
        f"  Antigravity (agy): {lvl['antigravity']}",
        "  Tramalia NO escribe esas configs (frontera con Gentle-AI): aplícalas tú.",
    ]
