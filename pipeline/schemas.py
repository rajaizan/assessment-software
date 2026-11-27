"""Data schemas for the pipeline. Every JSON file in data/ is checked against these.

There are no topics (ADR 0002). The question bank is the chapter exercise mapped to
the client's SLO codes, plus a few generated questions (ADR 0004).
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

QuestionType = Literal["mcq", "short", "long"]
MARKS: dict[str, int] = {"mcq": 1, "short": 2, "long": 5}
QuestionSource = Literal["exercise", "generated"]

# Which part of the chapter a text block belongs to. Only QUOTABLE_PARTS may be an
# answer's source; exercise questions and the SLO list are never quoted as facts.
TextPart = Literal["content", "slo_list", "key_points", "exercise"]
QUOTABLE_PARTS: frozenset[str] = frozenset({"content", "key_points"})


LevelGroup = Literal["lower", "middle", "higher"]
SLO_CODE_PATTERN = r"^S-\d{2}-[A-Z]-\d{2}$"  # client's code, e.g. S-07-A-06


class LevelGroups(BaseModel):
    """data/levels.json: the client's cognitive levels, grouped for difficulty presets."""

    model_config = ConfigDict(extra="forbid")

    source: str
    groups: dict[LevelGroup, list[str]]

    @model_validator(mode="after")
    def every_group_once(self) -> "LevelGroups":
        if set(self.groups) != {"lower", "middle", "higher"}:
            raise ValueError("levels.json needs exactly the groups lower, middle, higher")
        names = [name for names in self.groups.values() for name in names]
        if not all(names) or len(names) != len(set(names)):
            raise ValueError("each level name must be non-empty and in exactly one group")
        return self

    def group_of(self, level: str) -> LevelGroup | None:
        for group, names in self.groups.items():
            if level in names:
                return group
        return None


class Slo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-slo\d{2}$")
    number: int = Field(ge=1)
    text: str = Field(min_length=10)
    code: str = Field(pattern=SLO_CODE_PATTERN)  # from the client's coded SLO list
    level: str = Field(min_length=1)  # cognitive level from the client's list
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
        level_of_code: dict[str, str] = {}
        for slo in slos:
            known = level_of_code.setdefault(slo.code, slo.level)
            if known != slo.level:
                raise ValueError(f"{slo.code} has two different levels: {known} and {slo.level}")
        return slos

    def unknown_levels(self, levels: LevelGroups) -> list[str]:
        """Levels used here that are not in levels.json (must be empty)."""
        return sorted({s.level for s in self.slos if levels.group_of(s.level) is None})


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


FIGURE_PATTERN = r"^figures/ch\d{2}-[a-z0-9-]+\.png$"  # relative to web/public/


class ExerciseItem(BaseModel):
    """One question of the chapter's own exercise, copied exactly as printed."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-ex-[a-z]\d{2}$")  # e.g. ch01-ex-b05 = section B, question 5
    section: str = Field(pattern=r"^[A-Z]$")
    number: int = Field(ge=1)
    type: QuestionType
    text: str = Field(min_length=5)
    options: list[str] = Field(default_factory=list)
    question_page: int = Field(ge=1)
    figure: str | None = Field(default=None, pattern=FIGURE_PATTERN)

    @model_validator(mode="after")
    def options_for_type(self) -> "ExerciseItem":
        if (self.type == "mcq") != bool(self.options) or (self.options and len(self.options) != 4):
            raise ValueError("an exercise MCQ has exactly 4 options; other types have none")
        for value in (self.text, *self.options):
            if "UNREADABLE" in value or re.search(r"\[[^\]]*\?", value):
                raise ValueError(f"cut-off text must be read from the book first: {value!r}")
        return self


class ChapterExercise(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: int = Field(ge=1, le=12)
    source: str
    items: list[ExerciseItem] = Field(min_length=1)


class FigureCrop(BaseModel):
    """data/chXX/figures.json entry: which page image and pixel box a figure is cut from."""

    model_config = ConfigDict(extra="forbid")

    file: str = Field(pattern=FIGURE_PATTERN)
    pdf_page: int = Field(ge=1)
    box: tuple[int, int, int, int]  # left, top, right, bottom in the page image's pixels
    item: str = Field(pattern=r"^ch\d{2}-ex-[a-z]\d{2}$")  # exercise item that shows it


def generated_note(code: str, all_codes_covered: bool) -> str:
    """The exact bracketed note a generated question must carry (CLAUDE.md bank rule 5)."""
    reason = "extra MCQ" if all_codes_covered else "not covered in exercise"
    return f"(Newly generated - SLO {code}, {reason})"


class AnswerSource(BaseModel):
    """Where an answer comes from: a printed page and the exact words on it."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    excerpt: str = Field(min_length=15)


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^ch\d{2}-q\d{3}$")
    chapter: int = Field(ge=1, le=12)
    type: QuestionType
    text: str = Field(min_length=5)
    options: list[str] = Field(default_factory=list)
    answer: str = Field(min_length=1)
    marks: int
    slo_ids: list[str] = Field(min_length=1)  # client codes; the first is the main one
    cognitive_level: str = Field(min_length=1)  # = level of the first code
    source: QuestionSource
    generated_note: str = ""  # empty for exercise questions
    question_page: int = Field(ge=1)  # exercise: page it is printed on; generated: page it is based on
    answer_sources: list[AnswerSource] = Field(min_length=1)
    figure: str | None = Field(default=None, pattern=FIGURE_PATTERN)
    review_status: Literal["pending", "approved", "rejected"] = "pending"
    review_note: str = ""

    @field_validator("slo_ids")
    @classmethod
    def codes_ok(cls, codes: list[str]) -> list[str]:
        for code in codes:
            if not re.match(SLO_CODE_PATTERN, code):
                raise ValueError(f"{code!r} is not an SLO code like S-07-A-01")
        if len(codes) != len(set(codes)):
            raise ValueError("slo_ids must not repeat a code")
        return codes

    @model_validator(mode="after")
    def rules_for_type_and_source(self) -> "Question":
        if self.marks != MARKS[self.type]:
            raise ValueError(f"a {self.type} question is worth {MARKS[self.type]} mark(s)")
        if self.type == "mcq":
            if len(self.options) != 4:
                raise ValueError("an MCQ needs exactly 4 options")
            if len({o.strip().lower() for o in self.options}) != 4:
                raise ValueError("MCQ options must all be different")
            if self.answer not in self.options:
                raise ValueError("MCQ answer must be one of the options, word for word")
        elif self.options:
            raise ValueError(f"a {self.type} question must not have options")
        if self.source == "exercise" and self.generated_note:
            raise ValueError("an exercise question must not have a generated_note")
        if self.source == "generated" and not self.generated_note:
            raise ValueError("a generated question needs its generated_note")
        return self


class QuestionBank(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter: int = Field(ge=1, le=12)
    questions: list[Question]
