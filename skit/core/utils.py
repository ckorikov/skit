"""Shared core helpers. Depend on no other module, so anything may use them."""

from collections.abc import Set as AbstractSet

from slugify import slugify


def make_id(text: str, prefix: str = "", taken: AbstractSet[str] = frozenset()) -> str:
    """Build a readable id from free text: ``<prefix>-<slug of text>``.

    The prefix marks the kind — ``t`` for a topic, ``m`` for a module
    (``make_id("Basis", "t") -> "t-basis"``). Text is romanized to ASCII,
    so any script with a transliteration works — Latin (incl. accents),
    Cyrillic, Greek, CJK, Korean, and the consonantal scripts (Arabic,
    Hebrew); scripts without one, and symbols or emoji, are dropped. Text
    that romanizes to nothing raises. A candidate already in TAKEN gets a
    numeric suffix (``-2``, ``-3``, ...), the way a citation key gets a
    letter.
    """
    slug = slugify(text)
    if not slug:
        raise ValueError(f"cannot build an id from {text!r}")
    base = f"{prefix}-{slug}" if prefix else slug
    candidate, n = base, 1
    while candidate in taken:
        n += 1
        candidate = f"{base}-{n}"
    return candidate
