"""Tests for the shared helpers."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from skit.core.utils import make_id


@pytest.mark.parametrize(
    "text, prefix, expected",
    [
        ("Vector space", "", "vector-space"),
        ("Vector space", "t", "t-vector-space"),  # topic prefix
        ("Базис и размерность", "t", "t-bazis-i-razmernost"),  # transliterated
        ("  C++ & Co.  ", "m", "m-c-co"),  # module prefix; punctuation folded
    ],
)
def test_make_id_slugifies(text, prefix, expected):
    assert make_id(text, prefix) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Élève à côté", "eleve-a-cote"),  # Latin with accents
        ("Линейная алгебра", "lineinaia-algebra"),  # Cyrillic
        ("Γραμμική άλγεβρα", "grammike-algebra"),  # Greek
        ("线性代数", "xian-xing-dai-shu"),  # Chinese
        ("벡터 공간", "begteo-gonggan"),  # Korean
        ("الجبر الخطي", "ljbr-lkhty"),  # Arabic (consonantal)
        ("basis 🎓 vectors", "basis-vectors"),  # symbols/emoji dropped
    ],
)
def test_make_id_romanizes_any_script(text, expected):
    assert make_id(text) == expected


def test_make_id_disambiguates_against_taken():
    taken = {"t-basis", "t-basis-2"}
    assert make_id("Basis", "t", taken) == "t-basis-3"


def test_make_id_rejects_text_without_letters():
    with pytest.raises(ValueError):
        make_id("!!!", "t")


@given(st.text(min_size=1, max_size=20))
def test_make_id_is_a_valid_id(text):
    """Whatever comes out is usable as an Id (non-empty) or rejected outright."""
    try:
        made = make_id(text, "t")
    except ValueError:
        return
    assert made.startswith("t-") and len(made) > len("t-")
