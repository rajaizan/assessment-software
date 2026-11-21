"""Data schemas for the pipeline. Every JSON file in data/ is checked against these.

There are no topics (ADR 0002): questions link to one SLO, and each SLO lists the
book pages that teach it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

QuestionType = Literal["mcq", "true_false", "short"]
MARKS: dict[str, int] = {"mcq": 1, "true_false": 1, "short": 2}

# Which part of the chapter a text block belongs to. Only QUOTABLE_PARTS may be a
# question's source; exercise questions and the SLO list are never quoted as facts.
TextPart = Literal["content", "slo_list", "key_points", "exercise"]
QUOTABLE_PARTS: frozenset[str] = frozenset({"content", "key_points"})


class Slo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-slo\d{2}$")
    number: int = Field(ge=1)
    text: str = Field(min_length=10)
    pages: list[int] = Field(min_length=1)  # printed pages that teach this SLO

    @field_validator("text")
    @classmethod
    def no_placeholder(cls, value: str) -> str:
        if "UNREADABLE" in value:
            raise ValueError("SLO text must be fully typed from the book, not UNREADABLE")
        return value

    @field_validator("pages")
    @classmethod
    def sorted_unique(cls, pages: list[int]) -> list[int]:
        if pages != sorted(set(pages)) or pages[0] < 1:
            raise ValueError("SLO pages must be positive, sorted and without repeats")
        return pages


class ChapterSlos(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: int = Field(ge=1, le=12)
    title: str
    printed_page: int = Field(ge=1)
    source: str
    pages_status: Literal["proposed", "confirmed"]  # SLO page map: confirmed by Izan?
    slos: list[Slo] = Field(min_length=1)

    @field_validator("slos")
    @classmethod
    def numbered_in_order(cls, slos: list[Slo]) -> list[Slo]:
        for expected, slo in enumerate(slos, start=1):
            if slo.number != expected:
                raise ValueError(f"SLO numbers must be 1, 2, 3...; got {slo.number} at position {expected}")
        return slos


BLOCK_KINDS = ("heading", "paragraph", "list_item", "figure", "box", "table", "table_row")


class TextBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-p\d{3}-b\d{2}$")
    printed_page: int = Field(ge=1)
    pdf_page: int = Field(ge=1)
    part: TextPart
    kind: str
    text: str = Field(min_length=1)
    has_gaps: bool  # True if text contains [?...] or UNREADABLE marks

    @field_validator("kind")
    @classmethod
    def known_kind(cls, value: str) -> str:
        if value not in BLOCK_KINDS:
            raise ValueError(f"unknown block kind {value!r}")
        return value


class ChapterText(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: int = Field(ge=1, le=12)
    title: str
    source: str
    blocks: list[TextBlock] = Field(min_length=1)


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-q\d{3}$")
    chapter: int = Field(ge=1, le=12)
    slo_id: str = Field(pattern=r"^ch\d{2}-slo\d{2}$")
    type: QuestionType
    question: str = Field(min_length=5)
    options: list[str] = Field(default_factory=list)
    answer: str = Field(min_length=1)
    marks: int
    page: int = Field(ge=1)  # printed page number of the source excerpt
    source_excerpt: str = Field(min_length=15)
    review_status: Literal["pending", "approved", "rejected"] = "pending"
    review_note: str = ""

    @model_validator(mode="after")
    def rules_for_type(self) -> "Question":
        if self.marks != MARKS[self.type]:
            raise ValueError(f"a {self.type} question is worth {MARKS[self.type]} mark(s)")
        if self.type == "mcq":
            if len(self.options) != 4:
                raise ValueError("an MCQ needs exactly 4 options")
            if len({o.strip().lower() for o in self.options}) != 4:
                raise ValueError("MCQ options must all be different")
            if self.answer not in self.options:
                raise ValueError("MCQ answer must be one of the options, word for word")
        else:
            if self.options:
                raise ValueError(f"a {self.type} question must not have options")
            if self.type == "true_false" and self.answer not in ("True", "False"):
                raise ValueError("a true_false answer must be 'True' or 'False'")
        return self


class QuestionBank(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: int = Field(ge=1, le=12)
    questions: list[Question]
