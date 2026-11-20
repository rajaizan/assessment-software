"""Check every question in data/chXX/questions.json against the chapter.

Usage: .venv/Scripts/python.exe pipeline/validate_questions.py 1
Exit code 0 = all questions pass; 1 = at least one problem (each is printed).

Rules checked (see CLAUDE.md "Question rules"):
  - schema (types, 4 different MCQ options, answer is one of the options)
  - SLO id exists in slos.json; topic exists in text.json
  - page is inside the chapter; source_excerpt is found word for word on that page,
    inside the question's topic, and contains no cut-off/UNREADABLE marks
  - every word of question, options and answer is in the chapter text or in
    data/common_words.txt (simple plural/verb endings allowed)
  - short sentences (max MAX_SENTENCE_WORDS words)
  - no duplicate ids or duplicate question text
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from schemas import Question

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
class Context:
    chapter: int
    slo_ids: set[str]
    topic_ids: set[str]
    page_range: tuple[int, int]
    # (printed_page, section, text) for every block of the chapter
    blocks: list[tuple[int, str, str]]
    vocabulary: set[str] = field(default_factory=set)
    common: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.vocabulary:
            for _, _, text in self.blocks:
                clean = MARKERS.sub(" ", GAP.sub(" ", text))
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


def load_context(chapter: int) -> Context:
    folder = ROOT / "data" / f"ch{chapter:02d}"
    slos = json.loads((folder / "slos.json").read_text(encoding="utf-8-sig"))
    text = json.loads((folder / "text.json").read_text(encoding="utf-8-sig"))
    book = json.loads((ROOT / "data" / "book.json").read_text(encoding="utf-8-sig"))
    first, last = book["chapters"][chapter - 1]["printed_pages"]
    blocks = [(b["printed_page"], b["section"], b["text"]) for b in text["blocks"]]
    # SLO text is also chapter text (it is printed on page 1)
    vocab_blocks = blocks + [(first, "intro", s["text"]) for s in slos["slos"]]
    ctx = Context(
        chapter=chapter,
        slo_ids={s["id"] for s in slos["slos"]},
        topic_ids={t["id"] for t in text["topics"]},
        page_range=(first, last),
        blocks=vocab_blocks,
        common=load_common_words(ROOT / "data" / "common_words.txt"),
    )
    return ctx


def check_question(raw: dict, ctx: Context) -> list[str]:
    """Return a list of problems with one question (empty list = OK)."""
    try:
        q = Question.model_validate(raw)
    except ValidationError as exc:
        return [f"schema: {err['loc'][0] if err['loc'] else ''} {err['msg']}" for err in exc.errors()]

    problems: list[str] = []
    if q.chapter != ctx.chapter:
        problems.append(f"chapter is {q.chapter}, expected {ctx.chapter}")
    if q.slo_id not in ctx.slo_ids:
        problems.append(f"SLO {q.slo_id} does not exist in this chapter")
    if q.topic not in ctx.topic_ids:
        problems.append(f"topic {q.topic} does not exist in this chapter")

    first, last = ctx.page_range
    if not first <= q.page <= last:
        problems.append(f"page {q.page} is outside the chapter (pages {first}-{last})")

    excerpt = normalize(q.source_excerpt)
    if GAP.search(excerpt) or "[" in excerpt:
        problems.append("source_excerpt contains cut-off or UNREADABLE text")
    else:
        on_page = [(section, normalize(t)) for page, section, t in ctx.blocks if page == q.page]
        hits = [section for section, t in on_page if excerpt in t]
        if not hits:
            problems.append(f"source_excerpt not found word for word on page {q.page}")
        elif q.topic not in hits:
            problems.append(f"source_excerpt is on page {q.page} but not inside topic {q.topic}")

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
    for i, raw in enumerate(questions):
        qid = str(raw.get("id", f"#{i + 1}"))
        problems = check_question(raw, ctx)
        if qid in seen_ids:
            problems.append("duplicate id")
        text = normalize(str(raw.get("question", ""))).lower()
        if text in seen_text:
            problems.append("duplicate question text")
        seen_ids.add(qid)
        seen_text.add(text)
        if problems:
            report[qid] = problems
    return report


def main() -> int:
    chapter = int(sys.argv[1])
    path = ROOT / "data" / f"ch{chapter:02d}" / "questions.json"
    bank = json.loads(path.read_text(encoding="utf-8-sig"))
    report = check_bank(bank["questions"], load_context(chapter))
    total = len(bank["questions"])
    for qid, problems in report.items():
        for p in problems:
            print(f"FAIL {qid}: {p}")
    print(f"{total - len(report)} of {total} questions pass")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
