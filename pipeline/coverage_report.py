"""Check the exercise → SLO mapping and write the coverage report.

Usage: .venv/Scripts/python.exe pipeline/coverage_report.py 1
Reads  data/chXX/exercise.json, mapping.json, slos.json
Writes data/chXX/coverage.md (question → SLO table, counts per code, uncovered codes,
       which generation rule applies, answers at risk).
Stops with a message if an item is unmapped, a code is unknown, or a page is not one
of the mapped codes' pages.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from schemas import ChapterExercise, ChapterMapping, ChapterSlos

ROOT = Path(__file__).resolve().parent.parent
TYPES = ("mcq", "short", "long")
TYPE_NAMES = {"mcq": "MCQ", "short": "Short", "long": "Long"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


@dataclass
class Coverage:
    codes: dict[str, dict]  # code -> {"level", "book_slos", "pages", "counts": {type: n}}
    uncovered: list[str]
    problems: list[str]


def check(exercise: ChapterExercise, mapping: ChapterMapping, slos: ChapterSlos) -> Coverage:
    codes: dict[str, dict] = {}
    for slo in slos.slos:
        entry = codes.setdefault(slo.code, {"level": slo.level, "book_slos": [], "pages": set(),
                                            "counts": dict.fromkeys(TYPES, 0)})
        entry["book_slos"].append(slo.number)
        entry["pages"].update(slo.pages)

    problems = []
    item_ids = {item.id for item in exercise.items}
    for missing in sorted(item_ids - set(mapping.items)):
        problems.append(f"{missing} has no mapping")
    for extra in sorted(set(mapping.items) - item_ids):
        problems.append(f"mapping.json lists {extra}, which is not in exercise.json")
    for item in exercise.items:
        entry = mapping.items.get(item.id)
        if entry is None:
            continue
        unknown = [c for c in entry.slo_ids if c not in codes]
        if unknown:
            problems.append(f"{item.id}: unknown code(s) {unknown}")
            continue
        allowed = set().union(*(codes[c]["pages"] for c in entry.slo_ids))
        wrong = sorted(set(entry.pages) - allowed)
        if wrong:
            problems.append(f"{item.id}: page(s) {wrong} are not pages of {entry.slo_ids}")
        for code in entry.slo_ids:
            codes[code]["counts"][item.type] += 1

    uncovered = [c for c, e in codes.items() if not any(e["counts"].values())]
    return Coverage(codes=codes, uncovered=uncovered, problems=problems)


def report(chapter: int, exercise: ChapterExercise, mapping: ChapterMapping, cov: Coverage) -> str:
    lines = [f"# Chapter {chapter} – exercise coverage report", "",
             f"Mapping status: **{mapping.status}**. First code = main code (sets the level).", "",
             "## Question → SLO", "",
             "| # | Type | Question | Code(s) | Level | Book pages | Why |",
             "|---|---|---|---|---|---|---|"]
    for item in exercise.items:
        entry = mapping.items[item.id]
        text = item.text if len(item.text) <= 70 else item.text[:67] + "..."
        level = cov.codes[entry.slo_ids[0]]["level"]
        flag = " ⚠" if entry.answer_risk else ""
        lines.append(f"| {item.section}{item.number}{flag} | {TYPE_NAMES[item.type]} | {text} | "
                     f"{', '.join(entry.slo_ids)} | {level} | {', '.join(map(str, entry.pages))} | {entry.reason} |")

    lines += ["", "## Questions per SLO code", "",
              "| Code | Book SLO(s) | Level | MCQ | Short | Long | Total |", "|---|---|---|---|---|---|---|"]
    for code, e in cov.codes.items():
        c = e["counts"]
        lines.append(f"| {code} | {', '.join(map(str, e['book_slos']))} | {e['level']} | "
                     f"{c['mcq']} | {c['short']} | {c['long']} | {sum(c.values())} |")
    lines.append("")
    lines.append("A question with two codes is counted under both.")

    lines += ["", "## Uncovered SLO codes", ""]
    if cov.uncovered:
        lines += [f"- {code}" for code in cov.uncovered]
        lines += ["", "Rule: keep all exercise questions; write new questions **only for these codes**."]
    else:
        lines += ["None: the exercise covers every code.", "",
                  f"Rule: keep all exercise questions and add **1 extra MCQ per code** "
                  f"({len(cov.codes)} in total). No new short or long questions."]

    risky = [(item, mapping.items[item.id].answer_risk) for item in exercise.items if mapping.items[item.id].answer_risk]
    lines += ["", "## ⚠ Answers that may be hard to quote from the book (task 1.5)", ""]
    lines += [f"- **{i.section}{i.number}** {i.text} – {risk}" for i, risk in risky] or ["None."]
    return "\n".join(lines) + "\n"


def main() -> int:
    chapter = int(sys.argv[1])
    folder = ROOT / "data" / f"ch{chapter:02d}"
    exercise = ChapterExercise(**read_json(folder / "exercise.json"))
    mapping = ChapterMapping(**read_json(folder / "mapping.json"))
    slos = ChapterSlos(**read_json(folder / "slos.json"))
    cov = check(exercise, mapping, slos)
    if cov.problems:
        for p in cov.problems:
            print(f"FAIL {p}")
        return 1
    (folder / "coverage.md").write_text(report(chapter, exercise, mapping, cov), encoding="utf-8")
    print(f"Chapter {chapter}: {len(exercise.items)} items mapped; uncovered codes: {cov.uncovered or 'none'} -> coverage.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
