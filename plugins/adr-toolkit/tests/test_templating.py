import pytest

from adr_toolkit.templating import substitute


def test_substitutes_tokens_from_context() -> None:
    text = "# {{title}} for {{project}}\nPackage: {{package}}"
    ctx = {"title": "ADR", "project": "mise", "package": "com.robsartin.mise"}

    assert substitute(text, ctx) == "# ADR for mise\nPackage: com.robsartin.mise"


def test_unknown_token_raises() -> None:
    with pytest.raises(KeyError):
        substitute("hello {{missing}}", {"project": "mise"})
