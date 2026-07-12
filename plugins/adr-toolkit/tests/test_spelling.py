"""Guard: shipped prose uses American, not British, English spellings.

The packs are the source of truth; docs/adr and the top-level markdown are
hand-committed. examples/ is covered separately by the gen-examples drift check.
"""

import re
from pathlib import Path

from conftest import REPO

# Whole British spellings we normalize to American. Kept as exact words so that
# American look-alikes (e.g. "realistic", "analysis") never match.
BRITISH_WORDS = [
    "behaviour",
    "behaviours",
    "colour",
    "colours",
    "coloured",
    "colourful",
    "practise",
    "practises",
    "practising",
    "practised",
    "centralise",
    "centralised",
    "centralises",
    "centralising",
    "centralisation",
    "decentralise",
    "decentralised",
    "utilise",
    "utilised",
    "utilising",
    "utilisation",
    "synchronise",
    "synchronised",
    "synchronising",
    "synchronisation",
    "realise",
    "realised",
    "realises",
    "realising",
    "realisation",
    "penalise",
    "penalised",
    "penalising",
    "minimise",
    "minimised",
    "minimising",
    "minimisation",
    "maximise",
    "maximised",
    "maximising",
    "maximisation",
    "organise",
    "organised",
    "organising",
    "organisation",
    "prioritise",
    "prioritised",
    "prioritising",
    "optimise",
    "optimised",
    "optimising",
    "optimisation",
    "normalise",
    "normalised",
    "normalising",
    "serialise",
    "serialised",
    "serialising",
    "serialisation",
    "initialise",
    "initialised",
    "initialising",
    "initialisation",
    "customise",
    "customised",
    "categorise",
    "categorised",
    "summarise",
    "summarised",
    "recognise",
    "recognised",
    "standardise",
    "standardised",
    "specialise",
    "specialised",
    "generalise",
    "generalised",
    "emphasise",
    "emphasised",
    "analyse",
    "analysed",
    "analyses",
    "analysing",
    "licence",
    "defence",
    "offence",
    "pretence",
    "artefact",
    "artefacts",
    "catalogue",
    "catalogues",
    "modelling",
    "cancelled",
    "cancelling",
    "labelled",
    "signalling",
    "favour",
    "favourite",
    "honour",
    "grey",
    "whilst",
]

_PATTERN = re.compile(r"\b(" + "|".join(BRITISH_WORDS) + r")\b", re.IGNORECASE)


def _shipped_text_files() -> list[Path]:
    files: list[Path] = []
    files += sorted((REPO / "packs").rglob("*.md"))
    files += sorted((REPO / "docs" / "adr").rglob("*.md"))
    files += sorted((REPO / "src").rglob("*.py"))
    files += [REPO / "README.md", REPO / "skills" / "adr-toolkit" / "SKILL.md"]
    return files


def test_no_british_spellings_in_shipped_prose() -> None:
    offenders: list[str] = []
    for path in _shipped_text_files():
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            for match in _PATTERN.finditer(line):
                rel = path.relative_to(REPO)
                offenders.append(f"{rel}:{lineno}: {match.group(0)}")

    assert not offenders, "British spellings found; use American English:\n" + "\n".join(offenders)
