"""Core entities and the attribute system."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Scalar = str | int | float | bool
type Value = Scalar | list[Value] | dict[str, Value]

Id = Annotated[str, Field(min_length=1)]
Weight = Annotated[float, Field(ge=0.0, le=1.0)]


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Named(Frozen):
    title: str = Field(min_length=1)
    description: str | None = None


def _require_unique(keys, what: str) -> None:
    if len(keys) != len(set(keys)):
        raise ValueError(f"{what} must be unique")


class Evidence(Frozen):
    """A knowledge check: a question, optionally with a reference answer.

    Accepts a bare string (self-check) or a single ``{question: answer}``
    pair; an empty answer is always ``None``.
    """

    question: str
    answer: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _expand_shorthand(cls, v):
        if isinstance(v, str):
            return {"question": v}
        if isinstance(v, dict) and len(v) == 1 and "question" not in v:
            ((q, a),) = v.items()
            return {"question": q, "answer": a}
        return v

    @field_validator("answer")
    @classmethod
    def _blank_is_none(cls, v: str | None) -> str | None:
        return v or None


class Topic(Named):
    id: Id
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @field_validator("evidence")
    @classmethod
    def _unique_questions(cls, v: tuple[Evidence, ...]) -> tuple[Evidence, ...]:
        _require_unique([e.question for e in v], "question texts within a topic")
        return v


class Relation(Frozen):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    from_: str = Field(alias="from", min_length=1)
    to: str = Field(min_length=1)
    weight: Weight = 1.0
    description: str | None = None


class Module(Named):
    id: Id
    topics: tuple[Id, ...] = Field(min_length=1)

    @field_validator("topics")
    @classmethod
    def _unique_topics(cls, v: tuple[Id, ...]) -> tuple[Id, ...]:
        _require_unique(v, "topics within a module")
        return v


class Curriculum(Named):
    pass


class TopicInSyllabus(Frozen):
    topic: Id
    kind: Literal["required", "optional"]
    module: Id | None = None
    weight: Weight | None = None


type SyllabusLevel = tuple[TopicInSyllabus, ...]


class Syllabus(Named):
    id: Id
    content: tuple[SyllabusLevel, ...] = ()

    @field_validator("content")
    @classmethod
    def _unique_topics(cls, v: tuple[SyllabusLevel, ...]) -> tuple[SyllabusLevel, ...]:
        _require_unique([t.topic for level in v for t in level], "topics within a syllabus")
        return v
