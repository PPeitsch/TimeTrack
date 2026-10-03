"""Recognize the columns of an imported report from their headers."""

import re
from typing import Optional

# Header words for each column, matched as whole words: a substring match on
# "in" / "out" would also hit headers like "Login method" or "Checkout notes".
COLUMN_WORDS = {
    "date": {"fecha", "date", "day", "dia", "día"},
    "entry": {"entrada", "ingreso", "in", "entry", "start"},
    "exit": {"salida", "egreso", "out", "exit", "end"},
    "obs": {"observacion", "observación", "observaciones", "obs", "note", "notes"},
}


def column_kind(header: str) -> Optional[str]:
    """Return which column a header names ("date", "entry", ...), if any."""
    words = set(re.findall(r"\w+", header.lower()))
    for kind, names in COLUMN_WORDS.items():
        if words & names:
            return kind
    return None
