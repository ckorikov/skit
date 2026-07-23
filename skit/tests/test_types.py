"""Tests for core types.

Types are immutable (frozen) value objects, so per type we cover:

- Create & validate — construction plus the model invariants.
- Serialize / deserialize — dict and JSON round-trips.
- Update — copy-on-write via ``model_copy`` (there is no in-place update;
  delete is a storage concern, not a value-type one).
- Algebra — value equality/inequality, hashing, immutability.
"""

from typing import Literal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from skit.core.types import (
    Curriculum,
    Evidence,
    Module,
    Relation,
    Syllabus,
    SyllabusLevel,
    Topic,
    TopicInSyllabus,
)


# --- builders (explicit constructors) -------------------------------------


def evidence(question="q", answer=None) -> Evidence:
    return Evidence(question=question, answer=answer)


def topic(*evidence) -> Topic:
    """Topic from raw evidence (strings and/or {question: answer} pairs)."""
    items = tuple(Evidence.model_validate(e) for e in evidence)
    return Topic(id="t", title="T", evidence=items)


def relation(**fields) -> Relation:
    """Relation edge, defaulting to a->b; override "from", "to", "weight", ..."""
    return Relation(**{"from": "a", "to": "b", **fields})


def module(*topics) -> Module:
    return Module(id="m", title="M", topics=topics)


def curriculum(**fields) -> Curriculum:
    return Curriculum(**fields)


def tis(
    topic="t", kind: Literal["required", "optional"] = "required", **fields
) -> TopicInSyllabus:
    return TopicInSyllabus(topic=topic, kind=kind, **fields)


def level(*topics) -> SyllabusLevel:
    """One syllabus level from (topic_id, kind) pairs."""
    return tuple(TopicInSyllabus(topic=t, kind=k) for t, k in topics)


def syllabus(*levels) -> Syllabus:
    return Syllabus(id="s", title="S", content=levels)


@pytest.fixture(
    params=[
        evidence(),
        topic("q"),
        relation(),
        module("t"),
        curriculum(),
        tis(),
        syllabus(level(("t", "required"))),
    ],
    ids=lambda s: type(s).__name__,
)
def skit_type_instance(request):
    """One representative instance of each entity type, for the generic tests."""
    return request.param


# ==========================================================================
# Create & validate
# ==========================================================================

# strategy factories (functions, not module constants — @given can't take a fixture)


def texts():
    return st.text(min_size=1, max_size=20)


def out_of_unit():
    return st.floats().filter(lambda x: not (0.0 <= x <= 1.0))


@st.composite
def evidence_lists(draw):
    """Mixed evidence forms (self-check strings + question:answer pairs), unique questions."""
    questions = draw(st.lists(texts(), min_size=1, max_size=5, unique=True))
    return [
        q if draw(st.booleans()) else {q: draw(st.text())}  # str self-check | q:a pair
        for q in questions
    ]


@given(evidence_lists())
def test_topic_normalizes_and_keeps_questions_unique(raw):
    questions = [e.question for e in topic(*raw).evidence]
    assert len(questions) == len(set(questions))


def test_evidence_empty_answer_equals_bare_string():
    # invariant: a pair with an empty answer equals a bare string question
    assert evidence("q", "") == evidence("q")
    assert topic({"q": ""}) == topic("q")


def test_topic_empty_evidence_rejected():
    with pytest.raises(ValidationError):
        topic()


def test_topic_duplicate_question_rejected():
    with pytest.raises(ValidationError):
        topic("q", "q")


@given(st.floats(min_value=0.0, max_value=1.0))
def test_relation_weight_in_range_ok(w):
    assert relation(weight=w).weight == w


@given(out_of_unit())
def test_relation_weight_out_of_range_rejected(w):
    with pytest.raises(ValidationError):
        relation(weight=w)


def test_relation_defaults_hard():
    assert relation().weight == 1.0


def test_module_duplicate_topic_rejected():
    with pytest.raises(ValidationError):
        module("t", "t")


def test_syllabus_duplicate_topic_rejected():
    with pytest.raises(ValidationError):
        syllabus(level(("t", "required")), level(("t", "optional")))


# ==========================================================================
# Serialize / deserialize
# ==========================================================================


def test_dict_roundtrip(skit_type_instance):
    assert (
        type(skit_type_instance).model_validate(skit_type_instance.model_dump())
        == skit_type_instance
    )


def test_json_roundtrip(skit_type_instance):
    assert (
        type(skit_type_instance).model_validate_json(
            skit_type_instance.model_dump_json()
        )
        == skit_type_instance
    )


# ==========================================================================
# Update (copy-on-write)
# ==========================================================================


@pytest.mark.parametrize(
    "original, patch",
    [
        (evidence(), {"answer": "a2"}),
        (topic("q"), {"title": "T2"}),
        (relation(), {"weight": 0.5}),
        (module("t"), {"title": "M2"}),
        (curriculum(), {"description": "d2"}),
        (tis(), {"kind": "optional"}),
        (syllabus(level(("t", "required"))), {"title": "S2"}),
    ],
    ids=lambda case: type(case).__name__ if not isinstance(case, dict) else None,
)
def test_model_copy_updates_fields(original, patch):
    updated = original.model_copy(update=patch)
    assert updated is not original
    assert updated != original
    for field, value in patch.items():
        assert getattr(updated, field) == value


# ==========================================================================
# Algebra: equality, hashing, immutability
# ==========================================================================


def test_equal_and_hashable(skit_type_instance):
    twin = skit_type_instance.model_copy()
    assert (
        twin == skit_type_instance and twin is not skit_type_instance
    )  # value equality, not identity
    assert hash(twin) == hash(skit_type_instance)


@pytest.mark.parametrize(
    "a, b",
    [
        (evidence("q"), evidence("q2")),
        (evidence("q"), evidence("q", "a")),
        (topic("q"), topic("q2")),
        (relation(), relation(weight=0.5)),
        (relation(), relation(to="c")),
        (module("t"), module("t", "u")),
        (curriculum(), curriculum(description="d")),
        (tis(), tis(kind="optional")),
        (tis(), tis(topic="u")),
        (syllabus(level(("t", "required"))), syllabus(level(("u", "required")))),
    ],
    ids=lambda v: type(v).__name__,
)
def test_not_equal_when_fields_differ(a, b):
    # each pair differs in exactly one field
    assert a != b
    assert len({a, b}) == 2


def test_hashable_dedups_in_set(skit_type_instance):
    twin = type(skit_type_instance).model_validate(skit_type_instance.model_dump())
    assert len({skit_type_instance, twin}) == 1


def test_frozen_rejects_mutation(skit_type_instance):
    field = next(iter(type(skit_type_instance).model_fields))
    with pytest.raises(ValidationError):
        setattr(skit_type_instance, field, getattr(skit_type_instance, field))
