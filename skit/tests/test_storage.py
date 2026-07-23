"""Tests for the storage layer: package load/save round-trip and qualified views."""

import json
import string
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from skit.core.storage import Package, State
from skit.core.types import (
    Curriculum,
    Evidence,
    Module,
    Relation,
    Syllabus,
    Topic,
    TopicInSyllabus,
)


# --- helpers & fixtures ---------------------------------------------------


def _topic(id="t", **f):
    return Topic(id=id, title=id.upper(), evidence=(Evidence(question="q?"),), **f)


def _state():
    return State(
        curriculum=Curriculum(description="d"),
        active_syllabus="local:s",
        packages=(
            Package(
                name="local",
                topics=(_topic("a"), _topic("b", description="B")),
                relations=(
                    Relation.model_validate({"from": "a", "to": "b"}),
                    Relation.model_validate(
                        {"from": "a", "to": "linal:x", "weight": 0.6}
                    ),
                ),
                modules=(Module(id="m", title="M", topics=("a", "b")),),
                syllabi=(
                    Syllabus(
                        id="s",
                        title="S",
                        content=((TopicInSyllabus(topic="local:a", kind="required"),),),
                    ),
                ),
                attributes={
                    "a": {"literature": {"sources": []}},
                    "linal:x": {"assessment": {"scores": {}}},
                },
            ),
            Package(name="linal", topics=(_topic("x"),)),
        ),
    )


# --- strategy factories ---------------------------------------------------


def _names():
    return st.text(
        alphabet=string.ascii_lowercase + string.digits, min_size=1, max_size=6
    )


def _texts():
    return st.text(min_size=1, max_size=8)


def _topics():
    # evidence: unique question strings -> Evidence (unique questions per topic).
    return st.builds(
        lambda id, title, description, evidence: Topic(
            id=id, title=title, description=description, evidence=evidence
        ),
        id=_names(),
        title=_texts(),
        description=st.none() | _texts(),
        evidence=st.lists(_texts(), min_size=1, max_size=3, unique=True).map(
            lambda qs: tuple(Evidence(question=q) for q in qs)
        ),
    )


def _relations():
    return st.builds(
        lambda f, t, w, d: Relation.model_validate(
            {"from": f, "to": t, "weight": w, "description": d}
        ),
        f=_names(),
        t=_names(),
        w=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        d=st.none() | _texts(),
    )


def _modules():
    return st.builds(
        lambda id, title, topics: Module(id=id, title=title, topics=topics),
        id=_names(),
        title=_texts(),
        topics=st.lists(_names(), min_size=1, max_size=4, unique=True).map(tuple),
    )


def _syllabi():
    def build(id, title, topics, kinds):
        content = tuple(TopicInSyllabus(topic=t, kind=k) for t, k in zip(topics, kinds))
        return Syllabus(id=id, title=title, content=(content,) if content else ())

    return st.builds(
        build,
        id=_names(),
        title=_texts(),
        topics=st.lists(
            _names(), max_size=4, unique=True
        ),  # unique -> unique syllabus topics
        kinds=st.lists(st.sampled_from(("required", "optional")), max_size=4),
    )


def _values():
    scalars = (
        st.text(max_size=4)
        | st.integers()
        | st.booleans()
        | st.floats(allow_nan=False, allow_infinity=False)
    )
    return st.recursive(
        scalars,
        lambda c: st.lists(c, max_size=3) | st.dictionaries(_names(), c, max_size=3),
        max_leaves=5,
    )


def _attributes():
    namespaces = st.dictionaries(_names(), _values(), min_size=1, max_size=2)
    return st.dictionaries(_names(), namespaces, max_size=3)


def _packages():
    # >=1 topic per package: guarantees the package owns a topics file, which
    # fixes its load order (topics files are read first) to match save order.
    return st.builds(
        lambda name, topics, relations, modules, syllabi, attributes: Package(
            name=name,
            topics=topics,
            relations=relations,
            modules=modules,
            syllabi=syllabi,
            attributes=attributes,
        ),
        name=_names(),
        topics=st.lists(
            _topics(), min_size=1, max_size=3, unique_by=lambda t: t.id
        ).map(tuple),
        relations=st.lists(_relations(), max_size=3).map(tuple),
        modules=st.lists(_modules(), max_size=2, unique_by=lambda m: m.id).map(tuple),
        syllabi=st.lists(_syllabi(), max_size=2, unique_by=lambda s: s.id).map(tuple),
        attributes=_attributes(),
    )


def _states():
    return st.builds(
        lambda description, packages, active: State(
            curriculum=Curriculum(description=description),
            packages=packages,
            active_syllabus=active,
        ),
        description=st.none() | _texts(),
        packages=st.lists(
            _packages(), min_size=1, max_size=3, unique_by=lambda p: p.name
        ).map(tuple),
        active=st.none() | _names(),
    )


# --- round-trip & views ---------------------------------------------------


def test_roundtrip(tmp_path):
    s = _state()
    s.save(tmp_path)
    assert State.load(tmp_path) == s


def test_manifest_lists_only_present_files(tmp_path):
    _state().save(tmp_path)
    m = json.loads((tmp_path / "curriculum.json").read_text())
    assert m["topics"] == ["local.topics.json", "linal.topics.json"]
    assert m["modules"] == ["local.modules.json"]  # linal has none
    assert m["active_syllabus"] == "local:s"


def test_qualified_views():
    s = _state()
    assert set(s.topics()) == {"local:a", "local:b", "linal:x"}
    assert s.modules()["local:m"].topics == ("local:a", "local:b")
    # bare refs qualify against the relation's own package; qualified refs pass through
    assert {(r.from_, r.to) for r in s.relations()} == {
        ("local:a", "local:b"),
        ("local:a", "linal:x"),
    }
    # attribute keys qualify against the attribute file's package, not the entity's
    assert set(s.attributes()) == {"local:a", "linal:x"}


@settings(
    max_examples=100, deadline=None
)  # deadline off: each example does real file IO
@given(state=_states())
def test_save_load_roundtrip(state):
    """Any multi-package state survives save -> load unchanged, tmp files and all."""
    with tempfile.TemporaryDirectory() as d:
        state.save(d)
        assert not list(Path(d).glob("*.tmp"))  # atomic rename leaves no partials
        assert State.load(d) == state


# --- file and schema problems ---------------------------------------------


def test_load_missing_curriculum(tmp_path):
    with pytest.raises(FileNotFoundError):
        State.load(tmp_path)


def test_load_missing_package_file(tmp_path):
    # manifest names a file that was never written
    (tmp_path / "curriculum.json").write_text(
        json.dumps({"title": "C", "topics": ["ghost.topics.json"]})
    )
    with pytest.raises(FileNotFoundError):
        State.load(tmp_path)


def test_load_malformed_json(tmp_path):
    (tmp_path / "curriculum.json").write_text(
        json.dumps({"title": "C", "topics": ["p.topics.json"]})
    )
    (tmp_path / "p.topics.json").write_text("{ not valid json")
    with pytest.raises(json.JSONDecodeError):
        State.load(tmp_path)


def test_load_curriculum_malformed_json(tmp_path):
    (tmp_path / "curriculum.json").write_text("]not json[")
    with pytest.raises(json.JSONDecodeError):
        State.load(tmp_path)


@pytest.mark.parametrize(
    "topic_record",
    [
        {"id": "a"},  # missing title + evidence
        {"id": "a", "title": "A", "evidence": []},  # evidence must be non-empty
        {"id": "a", "title": "A", "evidence": ["q?"], "junk": 1},  # extra="forbid"
        {"title": "A", "evidence": ["q?"]},  # missing id
    ],
)
def test_load_invalid_entity_schema(tmp_path, topic_record):
    (tmp_path / "curriculum.json").write_text(
        json.dumps({"title": "C", "topics": ["p.topics.json"]})
    )
    (tmp_path / "p.topics.json").write_text(json.dumps([topic_record]))
    with pytest.raises(ValidationError):
        State.load(tmp_path)


def test_load_wrong_json_toplevel_type(tmp_path):
    # a topics file must be a list of records, not an object
    (tmp_path / "curriculum.json").write_text(
        json.dumps({"title": "C", "topics": ["p.topics.json"]})
    )
    (tmp_path / "p.topics.json").write_text(json.dumps({"id": "a"}))
    with pytest.raises((ValidationError, TypeError, AttributeError)):
        State.load(tmp_path)


def test_save_overwrites_stale_files(tmp_path):
    """Re-saving replaces a file in place; no leftover .tmp, content reflects the new state."""
    _state().save(tmp_path)
    smaller = State(
        curriculum=Curriculum(),
        packages=(Package(name="local", topics=(_topic("z"),)),),
    )
    smaller.save(tmp_path)
    assert not list(tmp_path.glob("*.tmp"))
    assert State.load(tmp_path) == smaller
