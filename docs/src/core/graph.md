# The curriculum graph

`skit` represents a curriculum as a directed graph: topics are the
vertices, and the dependencies between them are the edges. This page
defines that graph — its nodes and edges. The attributes that hold
every entity's properties are covered under
[Identifiers and Attributes](attributes.md); modules and study plans
under [Syllabus construction](syllabus.md). For the entities named
here, see [Concepts](concepts.md).

## The graph

Formally, the curriculum is a directed graph $G = (V, E)$ whose
vertices $V$ are topics and whose edges $E$ are weighted dependencies
between them. Edge weights — defined under [Edges](#edges) —
distinguish *hard* from *soft* edges and constrain which cycles the
graph may contain.

Topics may be grouped into modules. A module is not a vertex of the
graph — it is a labeling of vertices; modules and their use in
dependencies are covered under
[Syllabus construction](syllabus.md#modules).

## Edges

A dependency is an ordered pair (topic or module $\to$ topic or module)
with a weight $w \in [0, 1]$ and a description:

| Weight | Kind | Meaning |
| --- | --- | --- |
| $w = 1$ | hard | the predecessor topic must be studied first |
| $0 \lt w \lt 1$ | soft | the predecessor topic is recommended first; $w$ encodes the strength of the recommendation |
| $w = 0$ | none | the link is ignored during syllabus construction (equivalent to no link at all) |

If no weight is given, the link is treated as hard ($w = 1$).

!!! warning "Cycles and soft edges"

    Hard edges impose a strict study order, so cycles are constrained.
    The hard subgraph must be acyclic (a DAG); more strongly, no cycle
    in the $w > 0$ graph may contain a hard edge — a hard edge fixes an
    order that no chain of soft edges may close back on. Pure soft
    cycles (every edge soft) are allowed and express complementarity
    between topics.

The weight of a path $\pi = (e_1, \dots, e_k)$ is the product of its
edge weights:

$$w(\pi) = \prod_{i=1}^{k} w(e_i)$$

Hard edges ($w = 1$) are transparent to path weight; any soft edge
weakens everything higher up the dependency chain: the predecessors of
a topic linked to a target set through a soft edge are themselves
linked to that set no more strongly than that edge. The effective
weight of a topic $t$ with respect to a set of topics $S$ is the
maximum path weight from $t$ into $S$ over edges with $w > 0$:

$$\hat{w}(t, S) = \max_{\pi:\, t \rightsquigarrow S,\ w > 0} \; w(\pi)$$

The maximum is attained on a simple path: a cycle only decreases the
product, so cycles of soft edges do not affect the effective weight.

Soft links may express complementarity between topics and feed
[syllabus construction](syllabus.md#building-a-syllabus) as a source of
optional topics.

## Invariants

1. No cycle in the $w > 0$ graph contains a hard edge — equivalently,
   no hard edge lies inside a strongly connected component of that
   graph. Pure soft cycles are allowed; hard-subgraph acyclicity is the
   special case.
