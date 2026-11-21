"""Write a spot-check list for Izan (task 10b): every flagged question plus N random
approved questions per SLO, each with its answer, book page and quote.

Usage: .venv/Scripts/python.exe pipeline/spot_check.py 1 [per_slo=2] [seed=7]
Output: data/chXX/spot_check.md
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TYPE_NAMES = {"mcq": "MCQ", "true_false": "True/False", "short": "Short"}


def describe(q: dict) -> str:
    lines = [f"**{q['id']}** · {TYPE_NAMES[q['type']]} · book page {q['page']}", "", f"- Question: {q['question']}"]
    if q["options"]:
        lines.append("- Options: " + " / ".join(q["options"]))
    lines += [f"- Answer: {q['answer']}", f"- Book quote: \"{q['source_excerpt']}\""]
    if q["review_note"].startswith("flagged"):
        lines.append(f"- Why flagged: {q['review_note'].removeprefix('flagged: ')}")
    lines += ["- Your verdict: OK / Not OK (write why)", ""]
    return "\n".join(lines)


def main() -> None:
    chapter = int(sys.argv[1])
    per_slo = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 7)
    folder = ROOT / "data" / f"ch{chapter:02d}"
    questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))["questions"]
    slos = json.loads((folder / "slos.json").read_text(encoding="utf-8"))["slos"]

    flagged = [q for q in questions if q["review_status"] == "pending"]
    out = [f"# Chapter {chapter} spot-check (task 10b)", "",
           "Open the physical book at the page given. For each question, check that the answer is",
           "right and the wording is clear for students. Reply in chat with the ids that are Not OK.", "",
           f"## Flagged by Claude ({len(flagged)})", ""]
    out += [describe(q) for q in flagged]
    out += [f"## Random sample: {per_slo} approved questions per SLO", ""]
    for slo in slos:
        pool = [q for q in questions if q["slo_id"] == slo["id"] and q["review_status"] == "approved"]
        out += [f"### SLO {slo['number']}: {slo['text']}", ""]
        out += [describe(q) for q in rng.sample(pool, min(per_slo, len(pool)))]
    (folder / "spot_check.md").write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {folder / 'spot_check.md'}: {len(flagged)} flagged + {per_slo} per SLO")


if __name__ == "__main__":
    main()
