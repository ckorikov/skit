# Literature

Adds `sources` to topics and builds a recommended reading list for a
syllabus or module from them.

## Attributes

A topic gains one attribute, owned by Literature: `sources` — a list of
bibliographic records. Each record:

| Field | Value |
| --- | --- |
| type | book, article, inbook, online, … |
| author, title, year, publisher, url, … | bibliographic fields |
| chapter, pages | optional — a fragment (chapter or page range) |

Entry types and field names follow the
[BibTeX standard](https://en.wikipedia.org/wiki/BibTeX).

!!! note "Citation keys"

    A record stores no citation key; it is generated on export from the
    first author's last name and year — `knuth1984`, and on collision
    `knuth1984a`, `knuth1984b`.

## Reading list

The reading list of a syllabus or module is the union of its topics'
`sources`, deduplicated. It is not stored — computed live from the
topics' current sources (a syllabus fixes its topic set by snapshot,
but the sources stay live).

Two records are the **same source** when their type, title, authors,
and year match — call these four fields their *match key* (distinct
from the citation key above).

!!! warning "Conflicts"

    If two records share a match key but differ in other fields, that
    is a conflict — resolved manually (both are shown with their owning
    topics).

Sort order is chosen at generation time:

- **alphabetical** (authors, then title) — the only option for a
  module, since its topics are unordered;
- **by syllabus order** — "along the course"; a source belongs to the
  first topic (in syllabus order) where it appears.

For a syllabus the list splits by the snapshot's required/optional
flag: **primary** literature is the sources of required topics,
**supplementary** the sources of optional topics. A source in both goes
to primary.

## Capabilities

- Display the reading list for a syllabus or module in the chosen order.
- Export it to BibTeX (with citation-key generation).
