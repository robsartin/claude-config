"""Fill ``{{token}}`` placeholders in ADR templates from a context mapping."""

import re
from collections.abc import Mapping

_TOKEN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def substitute(text: str, context: Mapping[str, object]) -> str:
    """Replace every ``{{token}}`` in *text* with ``context[token]``.

    Raises KeyError if a token has no value, so an unresolved placeholder can
    never reach an emitted ADR.
    """

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise KeyError(key)
        return str(context[key])

    return _TOKEN.sub(replace, text)
