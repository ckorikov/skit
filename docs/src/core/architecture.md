# System architecture

`skit` is a core plus pluggable extensions. The core implements the base
model — [entities](concepts.md), the [graph](graph.md),
[attributes](attributes.md), [syllabus construction](syllabus.md) — and
nothing more. Extensions ([Literature](../extensions/literature.md),
[Assessment](../extensions/assessment.md)) add their own attributes and
operations on top. Dependencies point one way: extensions depend on the
core; the core knows nothing about concrete extensions.

## Core

The core holds the model, the attribute system, the graph engine
(module-sugar expansion, closures, effective weights, level
partitioning), and build.

It is purely functional: every operation takes the current state and
returns a result — a new state, a syllabus, a list of violations —
keeping no state of its own.

!!! note "Stateless core"

    Loading, saving, and the list of enabled extensions belong to the
    host (the composition root), passed into operations as arguments.
    Build is pure, so its result is reproducible from its recorded
    parameters and the order of extensions never matters.

## State

State is a set of JSON files grouped into packages; the file-name prefix
is the package: `local.topics.json` is package `local`. A package
contributes at most one file of each kind.

Ids are unique within a package; `package:id` is globally unique. Inside
a file a bare id resolves to that file's package; the qualified form is
needed only for other packages. Relations may cross packages
(`"from": "linal:top-basis", "to": "top-qft-intro"`), so a shared base of
topics is reusable across curricula.

!!! warning "Package is part of identity"

    Moving an entity to another package changes its qualified id and
    breaks references to it.

`<package>.topics.json` — graph vertices with their core attributes; a
topic references no module or syllabus.

```json
[
  {
    "id": "top-basis",
    "title": "...",
    "description": "...",
    "evidence": ["...", { "question": "answer" }]
  }
]
```

`<package>.relations.json` — edges as written: `{from, to, w?,
description?}`, where `from`/`to` are topics or modules, possibly
qualified. Module sugar is expanded by the graph engine on load. A
missing weight means hard ($w = 1$).

```json
[
  { "from": "top-vector-space", "to": "top-basis", "description": "..." },
  { "from": "top-determinant", "to": "top-eigen", "w": 0.6 }
]
```

`<package>.modules.json` — optional: module entities listing their
topics. "A topic belongs to at most one module" is checked by validation,
not structure.

```json
[
  { "id": "mod-vectors", "title": "...", "topics": ["top-vector-space", "top-basis"] }
]
```

`<package>.syllabi.json` — syllabus entities: `content` holds levels of
qualified topic ids with their marks (module, required/optional,
effective weight), plus prerequisites and build parameters. Records are
append-only — validation forbids editing after build.

```json
[
  {
    "id": "syl-20260722-eigen",
    "title": "...",
    "description": "...",
    "content": [ [ { "topic": "local:top-vector-space", "kind": "required" } ] ]
  }
]
```

`<package>.attributes.json` — non-core attributes, keyed by an id with a
namespace → values. The id may be qualified, so a package can annotate
entities of another package (a shared read-only package stays untouched
while the user's scores live in `local`). Two packages annotating the
same id under the same namespace is a validation error: every attribute
has exactly one source.

```json
{
  "linal:top-basis": {
    "assessment": { "scores": { "kostya/syl-20260722-eigen": [] } }
  },
  "top-qft-intro": {
    "literature": { "sources": [] }
  }
}
```

`curriculum.json` — the root: curriculum title/description, the manifest
of files, and the syllabus list with the active id. The manifest is
explicit — loaded packages are exactly the listed files, and validation
checks every qualified reference resolves.

```json
{
  "title": "...",
  "description": "...",
  "topics": ["local.topics.json", "linal.topics.json"],
  "relations": ["local.relations.json", "linal.relations.json"],
  "modules": ["linal.modules.json"],
  "syllabi": ["local.syllabi.json"],
  "attributes": ["local.attributes.json"],
  "active_syllabus": "syl-20260722-eigen"
}
```

## Extensions

An extension is a value: declarations plus pure functions. There is no
registry — the host holds the enabled list and passes it into operations.
Enabling is one config line; disabling deletes it and its data is kept
but ignored. The contract has four fields:

| Field | Signature | Role |
| --- | --- | --- |
| `namespace` | `str` | the one namespace it owns — the only place it writes attributes |
| `validate` | `(State) -> [Violation]` | its invariants, read-only; the core concatenates them with its own |
| `build_inject` | `(State, args) -> PartialBuildParams` | data merged into build args, e.g. `{excluded: ...}` for topics studied in a context |
| `services` | `{ name: (State, args) -> (Patch, Result) }` | its operations; each returns data plus a patch to its own namespace |

`build_inject` runs before build, so build stays pure. Merge rules are
per-parameter (for `excluded` — set union); an extension knows nothing
about other providers. A `services` patch touches only its own namespace,
so a service cannot alter structure or another namespace; a read-only
service returns an empty patch.

Interfaces (CLI, later HTTP/TUI) are thin adapters: parse args, call a
service, render. Core commands are top-level (`skit validate`,
`skit build`); extension commands live under the extension name
(`skit assessment next`). Shared rendering gives every command
human-readable output and `--json`.

The host loop: load state, run the operation with enabled extensions,
atomically save if a patch changed it (temp file, then rename), render.
An interrupted command never leaves half-written state.
