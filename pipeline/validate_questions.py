"""Check a chapter's question file against the chapter (schema v2, ADR 0004).

Usage: .venv/Scripts/python.exe pipeline/validate_questions.py 1 [file]
       file defaults to data/chXX/bank.json (e.g. data/ch01/exercise.json while building)
Exit code 0 = all questions pass; 1 = at least one problem (each is printed).

Rules checked (CLAUDE.md "Question-bank rules"):
  - schema: type mcq / short / long, fixed marks, MCQ options, note only on generated
  - every code in slo_ids exists in slos.json; cognitive_level = level of the first code
  - exercise questions: text (and MCQ options) found word for word in the chapter's
    exercise on question_page
  - generated questions: question_page is one of their codes' pages; text, options and
    answer use only chapter words (or data/common_words.txt) in short sentences
  - every answer source: page is one of the question's codes' pages, excerpt found word
    for word on that page in content / key_points, with no cut-off/UNREADABLE marks
  - answers use only chapter words (except an exercise MCQ answer, which is a book option)
  - figure (if any) exists in web/public/
  - bank level: no duplicate ids or text; generated questions follow the coverage rules
    (all codes covered → only MCQs, at most 1 per code; else only for uncovered codes)
    and carry the exact note; one book fact gives at most one generated question per type
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from schemas import QUOTABLE_PARTS, Question, generated_note

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
    code_pages: dict[str, set[int]]  # SLO code -> printed pages that teach it
    code_level: dict[str, str]  # SLO code -> cognitive level
    page_range: tuple[int, int]
    blocks: list[Block]
    common: set[str] = field(default_factory=set)
    vocabulary: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.vocabulary:
            for block in self.blocks:
                if block.part == "exercise":
                    continue  # exercise wording is not a source of facts or words
                clean = MARKERS.sub(" ", GAP.sub(" ", block.text))
                self.vocabulary.update(words(clean))
        self._stems = {stem(w) for w in self.vocabulary | self.common}

    def knows(self, word: str) -> bool:
        known = self.vocabulary | self.common
        if word in known or stem(word) in self._stems:
            return True
        # simple inflections: "face" is allowed if the chapter has "faces",
        # "stores" if it has "store", and so on. The base form must be in the chapter.
        for suffix in ("s", "es", "d", "ed", "ing"):
            if word + suffix in self.vocabulary:
                return True
            if word.endswith(suffix) and word[: -len(suffix)] in known:
                return True
        return False


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
    slos = read_json(folder / "slos.json")["slos"]
    text = read_json(folder / "text.json")
    first, last = read_json(ROOT / "data" / "book.json")["chapters"][chapter - 1]["printed_pages"]
    code_pages: dict[str, set[int]] = {}
    for slo in slos:  # one code may cover several book SLOs: join their pages
        code_pages.setdefault(slo["code"], set()).update(slo["pages"])
    return Context(
        chapter=chapter,
        code_pages=code_pages,
        code_level={slo["code"]: slo["level"] for slo in slos},
        page_range=(first, last),
        blocks=[Block(b["printed_page"], b["part"], b["text"]) for b in text["blocks"]],
        common=load_common_words(ROOT / "data" / "common_words.txt"),
    )


def unknown_words(texts: list[str], ctx: Context) -> list[str]:
    return sorted({w for t in texts for w in words(t) if not ctx.knows(w)})


def check_excerpt(excerpt: str, page: int, ctx: Context) -> str | None:
    excerpt = normalize(excerpt)
    if GAP.search(excerpt) or "[" in excerpt:
        return "contains cut-off or UNREADABLE text"
    hits = [b.part for b in ctx.blocks if b.page == page and excerpt in normalize(b.text)]
    if not hits:
        return f"not found word for word on page {page}"
    if not QUOTABLE_PARTS.intersection(hits):
        return f"comes from {hits[0]} text, which may not be quoted"
    return None


def check_question(raw: dict, ctx: Context) -> list[str]:
    """Return a list of problems with one question (empty list = OK)."""
    try:
        q = Question.model_validate(raw)
    except ValidationError as exc:
        return [f"schema: {err['loc'][0] if err['loc'] else ''} {err['msg']}" for err in exc.errors()]

    problems: list[str] = []
    if q.chapter != ctx.chapter:
        problems.append(f"chapter is {q.chapter}, expected {ctx.chapter}")

    unknown_codes = [c for c in q.slo_ids if c not in ctx.code_pages]
    for code in unknown_codes:
        problems.append(f"SLO {code} does not exist in this chapter")
    pages = set().union(*(ctx.code_pages.get(c, set()) for c in q.slo_ids))
    first_level = ctx.code_level.get(q.slo_ids[0])
    if first_level is not None and q.cognitive_level != first_level:
        problems.append(f"cognitive_level is {q.cognitive_level}, but {q.slo_ids[0]} is {first_level}")

    first, last = ctx.page_range
    if not first <= q.question_page <= last:
        problems.append(f"question_page {q.question_page} is outside the chapter (pages {first}-{last})")
    elif q.source == "exercise":
        printed = [normalize(b.text) for b in ctx.blocks if b.page == q.question_page and b.part == "exercise"]
        block = next((b for b in printed if normalize(q.text) in b), None)
        if block is None:
            problems.append(f"text not found word for word in the exercise on page {q.question_page}")
        else:
            missing = [o for o in q.options if normalize(o) not in block]
            if missing:
                problems.append(f"options not printed with this question: {missing}")
    elif not unknown_codes and q.question_page not in pages:
        problems.append(f"question_page {q.question_page} is not one of the pages of {q.slo_ids}")

    for n, src in enumerate(q.answer_sources, start=1):
        if not unknown_codes and src.page not in pages:
            problems.append(f"answer source {n}: page {src.page} is not one of the pages of {q.slo_ids}")
        trouble = check_excerpt(src.excerpt, src.page, ctx)
        if trouble:
            problems.append(f"answer source {n}: excerpt {trouble}")

    texts = [q.answer] if not (q.source == "exercise" and q.type == "mcq") else []
    if q.source == "generated":
        texts += [q.text, *q.options]
        for sentence in re.split(r"(?<=[.?!])\s+", q.text):
            if len(words(sentence)) > MAX_SENTENCE_WORDS:
                problems.append(f"sentence too long ({len(words(sentence))} words, max {MAX_SENTENCE_WORDS})")
    unknown = unknown_words(texts, ctx)
    if unknown:
        problems.append(f"words not in chapter or common list: {', '.join(unknown)}")

    if q.figure and not (ROOT / "web" / "public" / q.figure).is_file():
        problems.append(f"figure web/public/{q.figure} does not exist")
    return problems


def uncovered_codes(questions: list[dict], ctx: Context) -> list[str]:
    """Codes that no exercise question covers (these may get generated questions)."""
    covered = {c for q in questions if q.get("source") == "exercise" for c in q.get("slo_ids", [])}
    return sorted(set(ctx.code_pages) - covered)


def check_bank(questions: list[dict], ctx: Context) -> dict[str, list[str]]:
    """Return {question id: [problems]} for every question that has problems."""
    report: dict[str, list[str]] = {}
    uncovered = set(uncovered_codes(questions, ctx))
    all_covered = not uncovered
    extra_mcqs: Counter[str] = Counter()
    seen_ids: set[str] = set()
    seen_text: set[str] = set()
    seen_fact: set[tuple[str, str]] = set()
    for i, raw in enumerate(questions):
        qid = str(raw.get("id", f"#{i + 1}"))
        problems = check_question(raw, ctx)
        if qid in seen_ids:
            problems.append("duplicate id")
        text = normalize(str(raw.get("text", ""))).lower()
        if text in seen_text:
            problems.append("duplicate question text")
        seen_ids.add(qid)
        seen_text.add(text)

        codes = raw.get("slo_ids") or [""]
        if raw.get("source") == "generated":
            expected = generated_note(codes[0], all_covered)
            if raw.get("generated_note") != expected:
                problems.append(f"generated_note must be exactly {expected!r}")
            if all_covered:
                if raw.get("type") != "mcq":
                    problems.append("every code is covered by the exercise: only extra MCQs may be generated")
                extra_mcqs[codes[0]] += 1
                if extra_mcqs[codes[0]] > 1:
                    problems.append(f"only 1 extra MCQ per code; {codes[0]} already has one")
            elif not set(codes) <= uncovered:
                problems.append(f"generated questions are only for uncovered codes {sorted(uncovered)}")
            sources = raw.get("answer_sources") or [{}]
            fact = (normalize(str(sources[0].get("excerpt", ""))).lower(), str(raw.get("type", "")))
            if fact in seen_fact:
                problems.append("another generated question of the same type already uses this book fact")
            seen_fact.add(fact)
        if problems:
            report[qid] = problems
    return report


def main() -> int:
    chapter = int(sys.argv[1])
    folder = ROOT / "data" / f"ch{chapter:02d}"
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else folder / "bank.json"
    questions = read_json(path)["questions"]
    ctx = load_context(chapter)
    report = check_bank(questions, ctx)
    for qid, problems in report.items():
        for p in problems:
            print(f"FAIL {qid}: {p}")
    print(f"{len(questions) - len(report)} of {len(questions)} questions pass")
    uncovered = uncovered_codes(questions, ctx)
    print(f"Codes not covered by the exercise: {', '.join(uncovered) if uncovered else 'none'}")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
