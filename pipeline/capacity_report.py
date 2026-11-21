"""Show how many questions each SLO can supply, per type.

Usage: .venv/Scripts/python.exe pipeline/capacity_report.py 1

"approved" is what the app may use; "all" includes pending (not yet reviewed).
Rejected questions are never counted.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TYPES = ("mcq", "true_false", "short")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def capacity(chapter: int) -> tuple[list[dict], Counter, Counter]:
    folder = ROOT / "data" / f"ch{chapter:02d}"
    slos = read_json(folder / "slos.json")["slos"]
    questions = read_json(folder / "questions.json")["questions"]
    approved = Counter((q["slo_id"], q["type"]) for q in questions if q.get("review_status") == "approved")
    usable = Counter((q["slo_id"], q["type"]) for q in questions if q.get("review_status") != "rejected")
    return slos, approved, usable


def main() -> None:
    chapter = int(sys.argv[1])
    slos, approved, usable = capacity(chapter)
    header = "SLO".ljust(6) + "".join(t.rjust(14) for t in TYPES) + "total".rjust(10)
    print(f"Chapter {chapter} capacity (approved / all not rejected)")
    print(header)
    totals_a, totals_u = Counter(), Counter()
    for slo in slos:
        row = f"{slo['number']:<6}"
        for t in TYPES:
            a, u = approved[(slo["id"], t)], usable[(slo["id"], t)]
            totals_a[t] += a
            totals_u[t] += u
            row += f"{a:>8} / {u:<3}"
        row += f"{sum(approved[(slo['id'], t)] for t in TYPES):>8}"
        print(row)
    print("all".ljust(6) + "".join(f"{totals_a[t]:>8} / {totals_u[t]:<3}" for t in TYPES)
          + f"{sum(totals_a.values()):>8}")


if __name__ == "__main__":
    main()
