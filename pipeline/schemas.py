"""Data schemas for the pipeline. Every JSON file in data/ is checked against these."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Slo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-slo\d{2}$")
    number: int = Field(ge=1)
    text: str = Field(min_length=10)

    @field_validator("text")
    @classmethod
    def no_placeholder(cls, value: str) -> str:
        if "UNREADABLE" in value:
            raise ValueError("SLO text must be fully typed from the book, not UNREADABLE")
        return value


BLOCK_KINDS = ("heading", "paragraph", "list_item", "figure", "box", "table", "table_row")


class TextBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-p\d{3}-b\d{2}$")
    printed_page: int = Field(ge=1)
    pdf_page: int = Field(ge=1)
    section: str  # topic id like "1.4", or "intro", "key_points", "exercise"
    kind: str
    text: str = Field(min_length=1)
    has_gaps: bool  # True if text contains [?...] or UNREADABLE marks

    @field_validator("kind")
    @classmethod
    def known_kind(cls, value: str) -> str:
        if value not in BLOCK_KINDS:
            raise ValueError(f"unknown block kind {value!r}")
        return value


class Topic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^\d+\.\d+$")
    title: str
    printed_pages: list[int] = Field(min_length=2, max_length=2)


class ChapterText(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: int = Field(ge=1, le=12)
    title: str
    source: str
    topics: list[Topic] = Field(min_length=1)
    blocks: list[TextBlock] = Field(min_length=1)


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-q\d{3}$")
    chapter: int = Field(ge=1, le=12)
    topic: str = Field(pattern=r"^\d+\.\d+$")
    slo_id: str = Field(pattern=r"^ch\d{2}-slo\d{2}$")
    type: Literal["mcq", "short"]
    question: str = Field(min_length=5)
    options: list[str] = Field(default_factory=list)
    answer: str = Field(min_length=1)
    marks: int = Field(ge=1, le=5)
    page: int = Field(ge=1)  # printed page number of the source excerpt
    source_excerpt: str = Field(min_length=15)
    review_status: Literal["pending", "approved", "rejected"] = "pending"
    review_note: str = ""

    @model_validator(mode="after")
    def options_match_type(self) -> "Question":
        if self.type == "mcq":
            if len(self.options) != 4:
                raise ValueError("an MCQ needs exactly 4 options")
            if len({o.strip().lower() for o in self.options}) != 4:
                raise ValueError("MCQ options must all be different")
            if self.answer not in self.options:
                raise ValueError("MCQ answer must be one of the options, word for word")
        elif self.options:
            raise ValueError("a short-answer question must not have options")
        return self


class QuestionBank(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: int = Field(ge=1, le=12)
    questions: list[Question]


class ChapterSlos(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: int = Field(ge=1, le=12)
    title: str
    printed_page: int = Field(ge=1)
    source: str
    slos: list[Slo] = Field(min_length=1)

    @field_validator("slos")
    @classmethod
    def numbered_in_order(cls, slos: list[Slo]) -> list[Slo]:
        for expected, slo in enumerate(slos, start=1):
            if slo.number != expected:
                raise ValueError(f"SLO numbers must be 1, 2, 3...; got {slo.number} at position {expected}")
        return slos
