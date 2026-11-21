"""Check every question in data/chXX/questions.json against the chapter.

Usage: .venv/Scripts/python.exe pipeline/validate_questions.py 1
Exit code 0 = all questions pass; 1 = at least one problem (each is printed).

Rules checked (see CLAUDE.md "Question rules"; no topics, ADR 0002):
  - schema: type mcq / true_false / short, fixed marks, MCQ options, True/False answer
  - the SLO exists in slos.json, and the question's page is one of that SLO's pages
  - page is inside the chapter; source_excerpt is found word for word on that page
    in a quotable block (content / key_points, never exercise or the SLO list) and
    contains no cut-off/UNREADABLE marks
  - every word of question, options and answer is in the chapter text or in
    data/common_words.txt (simple plural/verb endings allowed)
  - short sentences (max MAX_SENTENCE_WORDS words)
  - bank level: no duplicate ids, no duplicate question text, and one book fact gives
    at most one question per type (source_excerpt + type unique), so no padding
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from schemas import QUOTABLE_PARTS, Question

ROOT = Path(__file__).resolve().parent.parent
GAP = re.compile(r"\[[^\]]*\?[^\]]*\]|UNREADABLE")
MARKERS = re.compile(r"\[BOX\b|\[FIG\]|\[TABLE\]")
WORD = re.compile(r"[a-z]+|\d+")
MAX_SENTENCE_WORDS = 25


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def stem(word: str) -> str:
    """Very small stemmer: lets 'leaves'/'leaf', 'cells'/'cell', 'conducts'/'conduct' match."""
    if len(word) <= 3:
        return word
    for suffix, repl in (("ies", "y"), ("ves", "f"), ("ing", ""), ("ed", ""), ("es", ""), ("s", ""), ("ly", "")):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)] + repl
    return word


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Block:
    page: int
    part: str
    text: str


@dataclass
class Context:
    chapter: int
    slo_pages: dict[str, set[int]]  # SLO id -> printed pages that teach it
    page_range: tuple[int, int]
    blocks: list[Block]
    common: set[str] = field(default_factory=set)
    vocabulary: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.vocabulary:
            for block in self.blocks:
                clean = MARKERS.sub(" ", GAP.sub(" ", block.text))
                self.vocabulary.update(words(clean))
        self._stems = {stem(w) for w in self.vocabulary | self.common}

    def knows(self, word: str) -> bool:
        return word in self.vocabulary or word in self.common or stem(word) in self._stems


def load_common_words(path: Path) -> set[str]:
    result = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip().lower()
        if line and not line.startswith("#"):
            result.add(line)
    return result


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_context(chapter: int) -> Context:
    folder = ROOT / "data" / f"ch{chapter:02d}"
    slos = read_json(folder / "slos.json")
    text = read_json(folder / "text.json")
    first, last = read_json(ROOT / "data" / "book.json")["chapters"][chapter - 1]["printed_pages"]
    return Context(
        chapter=chapter,
        slo_pages={s["id"]: set(s["pages"]) for s in slos["slos"]},
        page_range=(first, last),
        blocks=[Block(b["printed_page"], b["part"], b["text"]) for b in text["blocks"]],
        common=load_common_words(ROOT / "data" / "common_words.txt"),
    )


def check_question(raw: dict, ctx: Context) -> list[str]:
    """Return a list of problems with one question (empty list = OK)."""
    try:
        q = Question.model_validate(raw)
    except ValidationError as exc:
        return [f"schema: {err['loc'][0] if err['loc'] else ''} {err['msg']}" for err in exc.errors()]

    problems: list[str] = []
    if q.chapter != ctx.chapter:
        problems.append(f"chapter is {q.chapter}, expected {ctx.chapter}")

    first, last = ctx.page_range
    if not first <= q.page <= last:
        problems.append(f"page {q.page} is outside the chapter (pages {first}-{last})")

    slo_pages = ctx.slo_pages.get(q.slo_id)
    if slo_pages is None:
        problems.append(f"SLO {q.slo_id} does not exist in this chapter")
    elif q.page not in slo_pages:
        problems.append(f"page {q.page} is not one of {q.slo_id}'s pages {sorted(slo_pages)}")

    excerpt = normalize(q.source_excerpt)
    if GAP.search(excerpt) or "[" in excerpt:
        problems.append("source_excerpt contains cut-off or UNREADABLE text")
    else:
        hits = [b.part for b in ctx.blocks if b.page == q.page and excerpt in normalize(b.text)]
        if not hits:
            problems.append(f"source_excerpt not found word for word on page {q.page}")
        elif not QUOTABLE_PARTS.intersection(hits):
            problems.append(f"source_excerpt comes from {hits[0]} text, which may not be quoted")

    texts = [q.question, q.answer, *q.options]
    unknown = sorted({w for t in texts for w in words(t) if not ctx.knows(w)})
    if unknown:
        problems.append(f"words not in chapter or common list: {', '.join(unknown)}")

    for sentence in re.split(r"(?<=[.?!])\s+", q.question):
        if len(words(sentence)) > MAX_SENTENCE_WORDS:
            problems.append(f"sentence too long ({len(words(sentence))} words, max {MAX_SENTENCE_WORDS})")
    return problems


def check_bank(questions: list[dict], ctx: Context) -> dict[str, list[str]]:
    """Return {question id: [problems]} for every question that has problems."""
    report: dict[str, list[str]] = {}
    seen_ids: set[str] = set()
    seen_text: set[str] = set()
    seen_fact: set[tuple[str, str]] = set()
    for i, raw in enumerate(questions):
        qid = str(raw.get("id", f"#{i + 1}"))
        problems = check_question(raw, ctx)
        if qid in seen_ids:
            problems.append("duplicate id")
        text = normalize(str(raw.get("question", ""))).lower()
        if text in seen_text:
            problems.append("duplicate question text")
        fact = (normalize(str(raw.get("source_excerpt", ""))).lower(), str(raw.get("type", "")))
        if fact in seen_fact:
            problems.append("another question of the same type already uses this source_excerpt")
        seen_ids.add(qid)
        seen_text.add(text)
        seen_fact.add(fact)
        if problems:
            report[qid] = problems
    return report


def main() -> int:
    chapter = int(sys.argv[1])
    path = ROOT / "data" / f"ch{chapter:02d}" / "questions.json"
    bank = read_json(path)
    report = check_bank(bank["questions"], load_context(chapter))
    total = len(bank["questions"])
    for qid, problems in report.items():
        for p in problems:
            print(f"FAIL {qid}: {p}")
    print(f"{total - len(report)} of {total} questions pass")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
