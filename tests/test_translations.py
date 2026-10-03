"""The Spanish catalog must cover every message and keep placeholders intact."""

import re
from pathlib import Path

from babel.messages.mofile import read_mo
from babel.messages.pofile import read_po

CATALOG = Path(__file__).parent.parent / "app/translations/es/LC_MESSAGES/messages.po"
PLACEHOLDER = re.compile(r"%\(\w+\)s")


def test_spanish_catalog_is_complete_and_consistent():
    with open(CATALOG, "rb") as f:
        catalog = read_po(f)
    for message in catalog:
        if not message.id:
            continue
        assert message.string, f"Missing translation: {message.id!r}"
        assert sorted(PLACEHOLDER.findall(message.id)) == sorted(
            PLACEHOLDER.findall(message.string)
        ), f"Placeholder mismatch: {message.id!r}"


def test_compiled_catalog_matches_po():
    """messages.mo is versioned; it must be recompiled whenever the .po changes."""
    with open(CATALOG, "rb") as f:
        po = {m.id: m.string for m in read_po(f) if m.id}
    with open(CATALOG.with_suffix(".mo"), "rb") as f:
        mo = {m.id: m.string for m in read_mo(f) if m.id}
    assert mo == po, "Run: pybabel compile -d app/translations"
