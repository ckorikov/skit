# Syllabus construction

A syllabus is a course plan built from the
[curriculum graph](graph.md): the topics needed to reach a set of
target topics, ordered for study. This page covers modules, how they
are used in dependencies, and how a syllabus is structured and built.

## Modules

A module is a named set of topics united by a common learning goal.
A topic may belong to any number of modules (or none), and modules may
overlap. A module is not a vertex of the graph, but topics retain their
module membership: this is a labeling (clustering) of vertices used
when displaying a curriculum and a syllabus.

## Using modules in dependencies

Anywhere a topic is expected, a module may be given instead. For
dependencies this is syntactic sugar that expands into edges between
topics:

| Dependency | Expands to | Meaning |
| --- | --- | --- |
| $A \to M$ | $A \to t$ for every $t \in M$ | every topic of $M$ requires $A$ |
| $M \to B$ | $t \to B$ for every $t \in M$ | $B$ requires every topic of $M$ |
| $M_1 \to M_2$ | $t_1 \to t_2$ for every $t_1 \in M_1$, $t_2 \in M_2$ | every topic of $M_2$ requires every topic of $M_1$ |

where $A$, $B$ are topics; $M$, $M_1$, $M_2$ are modules; and $t$, $t_1$,
$t_2$ are topics of a module.

After expansion, dependencies exist only between topics; topic
membership in modules is preserved throughout. A module may also stand
in for a topic in the list of `targets` passed to
[build](#building-a-syllabus).

## Syllabus structure

A syllabus is a sequence of levels: an ordered list of sets of topics
(a partial order). Equivalently, it is a **topological sort** of its
topics over hard edges, grouped into levels. A topic's level is the
length of the longest path to it over hard edges within the syllabus
subgraph. Topics on the same level do not depend on one another through
hard edges and may be studied in any order.

!!! tip "Topological sort"

    A **topological sort** is an ordering of a directed acyclic graph
    in which every vertex comes after all of its predecessors. The
    syllabus levels are its layered form.

Within a level, topics are ordered deterministically:

1. Required topics first (included through hard closures), then
   optional topics (added through soft links).
2. Required topics are ordered by their target topic: a topic belongs
   to the first target topic (in `targets`-list order) whose closure
   contains it; topics of an earlier target topic come first.
3. Optional topics are ordered by decreasing effective weight.
4. If topics still tie, the one whose title comes first alphabetically
   goes first.

!!! tip "Hard closure"

    The **hard closure** (transitive closure over hard edges) of a
    topic is the topic together with all its hard prerequisites:
    everything it transitively depends on through hard edges.

Every topic in a syllabus carries marks: its module membership (the
modules it belongs to, if any), a required/optional flag, and — for
optional topics — an effective weight. A syllabus is a list of topics
with marks, not a list of modules: topics of one module may land on
different levels if there are dependencies between them. A view may
visually group adjacent topics of one module, but the model does not
guarantee this.

A syllabus is a snapshot: build fixes the set of topics, the
partitioning into levels, the order, and the marks. What is fixed does
not change with later changes to the curriculum. Everything else is
computed from the current state of the curriculum:

- topic attributes (titles, evidence, sources) are read at the moment
  of access;
- the hard predecessors of syllabus topics that are not in the
  syllabus form the syllabus prerequisites; they are computed
  dynamically and may change together with the curriculum.

## Building a syllabus

A syllabus is built by the function:

    build(G, targets?, max_topics?, max_optional?, excluded?) -> Syllabus

- `G: Graph` — the curriculum graph (after module expansion);
- `targets: list[Topic | Module]` — an ordered list of target topics
  and/or modules; a module stands for all its topics as targets, which
  inherit the module's position in the list. If omitted, `targets` is
  all sinks of the graph (topics that nothing depends on through hard
  edges);
- `max_topics: int` — an upper bound on the number of topics;
- `max_optional: int` — an upper bound on the number of optional topics;
- `excluded: set[Topic | Module]` — topics and/or modules excluded from
  the syllabus (for example, ones already studied); a module excludes
  all its topics.

Every parameter but `G` is optional.

The core does not interpret or store user state: state lives in the
attributes of extensions and reaches build only through injection
points — the function's arguments. This is how the
[Assessment](../extensions/assessment.md) extension injects topics
already studied in a context as `excluded`.

Construction rules:

1. The required part is the union of the transitive closures of the
   target topics over hard edges, minus `excluded`. An excluded topic
   counts as a satisfied predecessor and does not violate dependencies.
   Target topics are always included and cannot be excluded.
2. If the targets alone exceed `max_topics`, that is a criteria
   conflict — targets are mandatory, so the syllabus is not built.
   Otherwise, if the required part exceeds `max_topics`, it is trimmed
   to the `max_topics` most important topics (targets first, then their
   hard prerequisites by importance).
3. Optional candidates are topics outside the required part from which
   the required part is reachable over edges with $w > 0$. A candidate's
   priority is its [effective weight](graph.md#edges) with
   respect to the required part. A candidate is added atomically
   together with its hard closure among the optional candidates (minus
   `excluded` and topics already added) — a bundle. Bundles are added in
   decreasing order of the candidate's effective weight; a bundle that
   does not fit entirely within `max_optional` or `max_topics` is skipped.
   Ties in weight are broken by the alphabetical order of titles.

In short, build produces a topological sort of the required topics,
extends it with the optional ones, and groups the result into levels.

## Invariants

1. **Prerequisite completeness** — every hard predecessor of every
   syllabus topic is in the syllabus or excluded as already studied,
   except where the required part was trimmed to fit `max_topics`.
2. **Bounds** — a built syllabus holds at most `max_topics` topics and
   at most `max_optional` optional topics, when those limits are set.
3. **Snapshot integrity** — these hold as of build time. If later
   curriculum changes violate them (for example, a new hard edge
   between syllabus topics inverts the level order), the syllabus is
   flagged stale when displayed; it is not rebuilt automatically.
