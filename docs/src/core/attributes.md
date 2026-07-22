# Identifiers and Attributes

The [curriculum graph](graph.md) fixes only structure — nodes and
edges. Everything else — names, descriptions, evidence, and extension
data — is expressed as attributes of entities. This page covers both.

## Identifiers

Every entity (curriculum, syllabus, module, topic) has a unique
identifier that distinguishes it. The graph fixes only structure
(edges, module membership); all properties of entities, including the
required ones, are given by attributes.

## Attributes

Attributes are the properties of entities — a title, a description,
evidence, and so on. Each attribute of an entity is set at most once.

An attribute value is a tree: the leaves are scalars, and the inner
nodes group them into lists or maps. Formally:

```ebnf
value  = scalar | list | map ;
scalar = string | number | boolean ;
list   = "[" [ value { "," value } ] "]" ;
map    = "{" [ key ":" value { "," key ":" value } ] "}" ;
key    = string ;
```

Examples — letters stand for arbitrary scalars:

- **Scalar** — one leaf: `x`
- **List** — an ordered sequence: `[a, b, c]`
- **Map (tree)** — named branches addressed by a path:

    ```
    { p: { q: [a, b] },
      r: c }
    ```

    The path `p → q` leads to `[a, b]`. Different paths are independent
    subtrees, so branches do not interfere.

## Core attributes

The required attributes every entity must have, one table per entity.

**curriculum**

| Attribute | Value |
| --- | --- |
| title | name of the curriculum |
| description | free-text description |

**syllabus**

| Attribute | Value |
| --- | --- |
| title | name of the syllabus |
| description | free-text description |
| content | a sequence of levels of topic ids, each with its marks (module, required/optional, weight) |

**module**

| Attribute | Value |
| --- | --- |
| title | name of the module |
| description | free-text description |
| content | an unordered list of topics |

**topic**

| Attribute | Value |
| --- | --- |
| title | name of the topic |
| description | free-text description |
| evidence | a non-empty list of knowledge checks (see below) |

Each item of `evidence` is one of two kinds, which may be mixed in one
list:

- a string — a question with no reference answer (self-check);
- a key–value pair — a question (the key) with a reference answer or
  grading criterion (the value).

## Invariants

1. Every topic has non-empty evidence.
2. Question texts within a single topic are unique; a pair with an
   empty answer is equivalent to a string question.
3. Every attribute of every entity has exactly one owner — the base
   model or a single extension.
