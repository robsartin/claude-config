import re
from pathlib import Path

from conftest import REPO, emit_real

# ADRs that describe a mechanism — a cycle, a state machine, a flow, or an
# ownership boundary — rather than listing conventions. Each carries a diagram.
DIAGRAMMED: list[tuple[str, list[str]]] = [
    ("record-architecture-decisions", ["universal"]),
    ("use-test-driven-development", ["universal"]),
    ("pr-based-trunk-workflow", ["universal"]),
    ("mikado-method-for-changes", ["universal"]),
    ("observability-baseline", ["observability"]),
    ("service-conventions", ["service"]),
    ("d3-with-react", ["d3", "react"]),
    ("d3-with-vue", ["d3", "vue"]),
    ("d3-with-svelte", ["d3", "svelte"]),
    ("d3-with-plain-dom", ["d3", "plain-js"]),
]


def _emitted(tmp_path: Path, topic: str, packs: list[str]) -> str:
    written = emit_real(tmp_path / topic, packs)
    return next(p for p in written if p.stem[5:] == topic).read_text()


def test_mechanism_adrs_emit_a_mermaid_diagram(tmp_path: Path) -> None:
    """The diagram has to survive templating, not just exist in the pack source."""
    missing = [
        topic for topic, packs in DIAGRAMMED if "```mermaid" not in _emitted(tmp_path, topic, packs)
    ]

    assert not missing, f"expected a mermaid diagram in: {missing}"


def test_mermaid_blocks_avoid_template_token_lookalikes() -> None:
    """Mermaid's ``id{{Label}}`` hexagon is indistinguishable from a ``{{token}}``.

    ``templating.substitute`` matches ``{{\\w+}}`` and raises KeyError on an
    unknown name, so a single-word hexagon node crashes scaffolding for users.
    Ban the shape outright rather than relying on labels happening to contain
    a space.
    """
    offenders = []
    for path in sorted((REPO / "packs").rglob("*.md")):
        for block in re.findall(r"```mermaid\n(.*?)```", path.read_text(), re.DOTALL):
            if "{{" in block:
                offenders.append(str(path.relative_to(REPO)))

    assert not offenders, f"mermaid blocks must not contain '{{{{': {offenders}"


def test_diagrams_do_not_replace_the_prose(tmp_path: Path) -> None:
    """These ADRs land in repos whose viewer may not render mermaid, so a diagram
    illustrates the decision and never carries it alone."""
    for topic, packs in DIAGRAMMED:
        text = _emitted(tmp_path, topic, packs)
        without_diagrams = re.sub(r"```mermaid\n.*?```", "", text, flags=re.DOTALL)
        decision = without_diagrams.split("## Decision", 1)[1].split("##", 1)[0]

        assert len(decision.split()) > 60, f"{topic}: Decision is too thin without its diagram"
