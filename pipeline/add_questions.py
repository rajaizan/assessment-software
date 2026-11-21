"""Add a batch of new questions to data/chXX/questions.json, only if they all pass the validator.

Usage: .venv/Scripts/python.exe pipeline/add_questions.py 1 path/to/batch.json

Batch file = JSON list of short records:
  {"slo": 3, "type": "mcq", "q": "...", "options": [...], "answer": "...",
   "page": 13, "excerpt": "exact words from that page"}
The script fills in id, chapter, slo_id, marks and review_status ("pending").
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from schemas import MARKS
from validate_questions import check_bank, load_context, read_json

ROOT = Path(__file__).resolve().parent.parent


def expand(chapter: int, item: dict, number: int) -> dict:
    return {
        "id": f"ch{chapter:02d}-q{number:03d}",
        "chapter": chapter,
        "slo_id": f"ch{chapter:02d}-slo{item['slo']:02d}",
        "type": item["type"],
        "question": item["q"],
        "options": item.get("options", []),
        "answer": item["answer"],
        "marks": MARKS.get(item["type"], 0),
        "page": item["page"],
        "source_excerpt": item["excerpt"],
        "review_status": "pending",
        "review_note": "",
    }


def main() -> int:
    chapter, batch_path = int(sys.argv[1]), Path(sys.argv[2])
    bank_path = ROOT / "data" / f"ch{chapter:02d}" / "questions.json"
    bank = read_json(bank_path)
    start = max((int(q["id"][-3:]) for q in bank["questions"]), default=0) + 1
    batch = json.loads(batch_path.read_text(encoding="utf-8-sig"))
    new = [expand(chapter, item, start + i) for i, item in enumerate(batch)]

    report = check_bank(bank["questions"] + new, load_context(chapter))
    new_ids = {q["id"] for q in new}
    bad = {qid: p for qid, p in report.items() if qid in new_ids}
    if report.keys() - new_ids:
        print("Existing bank already has problems; fix those first.")
    if bad or report.keys() - new_ids:
        by_id = {q["id"]: q for q in new}
        for qid, problems in report.items():
            label = by_id[qid]["question"][:60] if qid in by_id else qid
            for p in problems:
                print(f"FAIL {qid} ({label}): {p}")
        print(f"Nothing saved. {len(bad)} of {len(new)} new questions have problems.")
        return 1

    bank["questions"].extend(new)
    bank_path.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Added {len(new)} questions ({new[0]['id']} to {new[-1]['id']}); bank now has {len(bank['questions'])}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
