# Assessment

Adds grading of topics by their knowledge checks (evidence), a score
log, and selection of the next topic to study with spaced repetition.
Evidence is part of the base model (a required topic attribute); the
extension adds grades on top of it.

## Attributes

A topic gains one attribute, owned by Assessment: `scores` — a
tree-shaped log. A path within it is the grading context (for example a
student and/or a syllabus); its leaf is a date-ordered list of records.
Each record:

| Field | Value |
| --- | --- |
| value | answer quality, from 0 (failed) to 1 (perfect) |
| date | the moment of grading |
| feedback | optional text explaining the grade |

!!! note "Contexts are independent"

    Paths within `scores` are disjoint, so the logs of different
    contexts do not interfere. A grade is given to the topic as a whole
    from its evidence answers; the reference answer, if any, is shown
    afterwards — no automatic checking.

From one context's log the repetition model derives:

- $\Delta$ — time since the last grade;
- $n$ — consecutive successful attempts back from the last (successful
  when $\text{value} \ge 0.6$; a failure resets the count).

A topic is **studied** in a context when its last grade there is
successful. Assessment injects studied topics into
[build](../core/syllabus.md#building-a-syllabus) as `excluded`.

## Capabilities

- Running a knowledge check over a syllabus, a module, or a single
  topic based on the evidence of the included topics.
- Keeping a score log across different contexts (students, syllabi).
- Computing which topics are studied in a context.
- Selecting the next topic to study with spaced repetition taken into
  account.

## Selecting the next topic

Candidates are determined from the logs of the chosen context:

- all syllabus topics that have grades in the context — regardless of
  whether the last attempt was successful;
- the next topic in the course — the first topic in syllabus order with
  no grades in the context (if there is one).

Syllabus order guarantees that all hard predecessors of the next topic
come before it, meaning they either already have grades or were
excluded at build time; a separate rule for admitting new topics is not
required. A topic whose last attempt was unsuccessful remains a
candidate on par with studied ones: its short half-life gives it high
priority, and it naturally competes for review.

The next topic is chosen from the candidates stochastically by its
forgetting probability (the model is below).

## The spaced repetition model

The model is built on the exponential forgetting curve[^ebbinghaus]:
without review the chance of recalling a topic decays with time, and
each successful review slows that decay. The steps below make this
precise.

### Probability of recall

The probability of recalling a topic after time $\Delta$[^settles]:

$$p = 2^{-\Delta / h}$$

where $h$ is the memory half-life: the time over which the probability
of recall drops to $0.5$.

<div data-plot="recall"></div>

A larger half-life $h$ flattens the curve — the topic is forgotten more
slowly. Each curve crosses $p = 0.5$ exactly at $\Delta = h$.

### Half-life

The half-life grows geometrically: each successful repetition
multiplies it by the ease factor $\mathrm{EF}$, borrowed from
SM-2[^wozniak], where it grows the review interval:

$$h = h_0 \cdot \mathrm{EF}^{\,n}$$

- $h_0$ — the initial half-life ($1$ day by default);
- $\mathrm{EF}$ — the SM-2 ease factor, the geometric growth rate
  ($\mathrm{EF} = 2.5$ by default, the standard SM-2 value).

<div data-plot="halflife"></div>

With defaults, each successful review multiplies $h$ by
$\mathrm{EF} = 2.5$, so it grows fast: $h = 1, 2.5, 6.25, \dots$ days.

### Topic priority

A topic's priority for display is its **forgetting probability** $f$ —
the probability that the topic has been forgotten, i.e. the complement
of the recall probability $p$[^ye]:

$$f = 1 - p = 1 - 2^{-\Delta / h}$$

For the next topic in the course (the log in the context is empty,
$\Delta$ undefined), $f = p_0$ ($p_0 = 0.7$ by default).

### Selection from candidates

Unlike deterministic schedulers (SM-2, FSRS), which show all topics
with $p$ below a threshold (usually $0.9$), the next topic is chosen
stochastically — Boltzmann (softmax) exploration[^softmax]:

$$P(i) = \frac{f_i^{\,\beta}}{\sum_j f_j^{\,\beta}}$$

where the sum is over the candidates and $\beta$ is the greediness
parameter: $\beta \to 0$ is a uniform random choice, $\beta \to \infty$
is the deterministic choice of the most-forgotten topic ($\beta = 3$ by
default).

<div data-plot="softmax"></div>

For the same five candidates, a larger $\beta$ concentrates the
probability on the most-forgotten topics; a smaller $\beta$ spreads it
out.

[^ebbinghaus]: Ebbinghaus, H. (1885). [*Über das Gedächtnis*](https://psychclassics.yorku.ca/Ebbinghaus/index.htm).
[^wozniak]: Woźniak, P. (1990). [Algorithm SM-2](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2). SuperMemo.
[^settles]: Settles, B., & Meeder, B. (2016). [A Trainable Spaced Repetition Model for Language Learning](https://aclanthology.org/P16-1174/). *Proceedings of ACL 2016*.
[^ye]: Ye, J., et al. (2022). [A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling](https://dl.acm.org/doi/10.1145/3534678.3539081). *Proceedings of KDD 2022*.
[^softmax]: [Softmax function](https://en.wikipedia.org/wiki/Softmax_function) — Boltzmann (softmax) exploration.
