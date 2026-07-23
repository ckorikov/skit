"""State: JSON packages + manifest."""

import json
from pathlib import Path

from pydantic import Field

from skit.core.types import (
    Curriculum,
    Frozen,
    Module,
    Relation,
    Syllabus,
    Topic,
    Value,
)

MODELS = {
    "topics": Topic,
    "relations": Relation,
    "modules": Module,
    "syllabi": Syllabus,
    "attributes": None,
}
Attributes = dict[str, dict[str, Value]]  # entity id -> namespace -> value


def _filename(name: str, kind: str) -> str:
    """A package's file for a kind: ``<name>.<kind>.json``."""
    return f"{name}.{kind}.json"


class Package(Frozen):
    """One package: the entities of a single file-name prefix."""

    name: str = Field(min_length=1)
    topics: tuple[Topic, ...] = ()
    relations: tuple[Relation, ...] = ()
    modules: tuple[Module, ...] = ()
    syllabi: tuple[Syllabus, ...] = ()
    attributes: Attributes = Field(default_factory=dict)

    def qualify_id(self, ref: str) -> str:
        """Resolve a possibly-bare id against this package."""
        return ref if ":" in ref else f"{self.name}:{ref}"


class State(Frozen):
    """The loaded curriculum: its root entity plus its packages.

    Pure value object; the view methods (:meth:`topics`, :meth:`relations`,
    ...) recompute ``package:id`` keys on demand and never mutate ``self``.
    """

    curriculum: Curriculum
    packages: tuple[Package, ...] = ()
    active_syllabus: str | None = None

    @classmethod
    def load(cls, root: Path | str) -> "State":
        root = Path(root)
        m = _read(root / "curriculum.json")
        files = {kind: m.get(kind, []) for kind in MODELS}
        return cls(
            curriculum=Curriculum(title=m["title"], description=m.get("description")),
            packages=tuple(
                _deserialize_package(name, _read_package(root, name, files))
                for name in _find_package_names(files)
            ),
            active_syllabus=m.get("active_syllabus"),
        )

    def save(self, root: Path | str) -> None:
        root = Path(root)
        written = [
            entry
            for pkg in self.packages
            for entry in _write_package(root, pkg.name, _serialize_package(pkg))
        ]
        _write(root / "curriculum.json", _build_manifest(self, written))

    def topics(self) -> dict[str, Topic]:
        return {p.qualify_id(t.id): t for p in self.packages for t in p.topics}

    def modules(self) -> dict[str, Module]:
        return {
            p.qualify_id(m.id): m.model_copy(
                update={"topics": tuple(p.qualify_id(t) for t in m.topics)}
            )
            for p in self.packages
            for m in p.modules
        }

    def relations(self) -> tuple[Relation, ...]:
        return tuple(
            r.model_copy(
                update={"from_": p.qualify_id(r.from_), "to": p.qualify_id(r.to)}
            )
            for p in self.packages
            for r in p.relations
        )

    def attributes(self) -> Attributes:
        out: Attributes = {}
        for p in self.packages:
            for entity_id, namespaces in p.attributes.items():
                out.setdefault(p.qualify_id(entity_id), {}).update(namespaces)
        return out


# --- deserialize / load ---------------------------------------------------


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_package(root: Path, name: str, files: dict[str, list[str]]) -> dict:
    """Raw json per kind for one package (None where the manifest omits a kind)."""
    out = {}
    for kind in MODELS:
        fn = _filename(name, kind)
        out[kind] = _read(root / fn) if fn in files[kind] else None
    return out


def _deserialize(kind: str, raw):
    """Inverse of _serialize: raw json -> entity tuple (or the attributes tree)."""
    if MODELS[kind] is None:
        return raw or {}
    return tuple(MODELS[kind].model_validate(x) for x in raw) if raw else ()


def _deserialize_package(name: str, raw: dict) -> Package:
    """Inverse of _serialize_package: raw json per kind -> Package."""
    fields = {kind: _deserialize(kind, raw[kind]) for kind in MODELS}
    return Package.model_validate({"name": name, **fields})


def _find_package_names(files: dict[str, list[str]]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(fn.split(".", 1)[0] for names in files.values() for fn in names)
    )


# --- serialize / save -----------------------------------------------------


def _serialize(pkg: Package, kind: str):
    if MODELS[kind] is None:  # attributes: an untyped tree, passed through as-is
        return pkg.attributes
    return [x.model_dump(by_alias=True, exclude_none=True) for x in getattr(pkg, kind)]


def _serialize_package(pkg: Package) -> dict:
    """Inverse of _deserialize_package: Package -> raw json per non-empty kind."""
    return {kind: data for kind in MODELS if (data := _serialize(pkg, kind))}


def _write_package(root: Path, name: str, raw: dict) -> list[tuple[str, str]]:
    """Write each kind's file; return its (kind, filename) manifest entry."""
    written = []
    for kind, data in raw.items():
        fn = _filename(name, kind)
        _write(root / fn, data)
        written.append((kind, fn))
    return written


def _build_manifest(state: State, files: list[tuple[str, str]]) -> dict:
    m: dict = {"title": state.curriculum.title}
    if (desc := state.curriculum.description) is not None:
        m["description"] = desc
    for kind in MODELS:
        m[kind] = [fn for k, fn in files if k == kind]
    if (syl := state.active_syllabus) is not None:
        m["active_syllabus"] = syl
    return m


def _write(path: Path, data) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)  # atomic: an interrupted save never leaves half-written state
