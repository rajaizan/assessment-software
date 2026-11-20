"""Turn Izan's typed data/chXX/slos.txt into a checked data/chXX/slos.json.

Usage: .venv/Scripts/python.exe pipeline/slos_to_json.py 1
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from schemas import ChapterSlos

ROOT = Path(__file__).resolve().parent.parent
LINE = re.compile(r"^(\d+)\.\s+(.+)$")


def convert(chapter: int) -> ChapterSlos:
    folder = ROOT / "data" / f"ch{chapter:02d}"
    book = json.loads((ROOT / "data" / "book.json").read_text(encoding="utf-8-sig"))
    info = book["chapters"][chapter - 1]

    slos = []
    for raw in (folder / "slos.txt").read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = LINE.match(line)
        if not match:
            raise SystemExit(f"Line is not 'N. text': {line!r}")
        number = int(match.group(1))
        text = re.sub(r"\s+", " ", match.group(2)).strip()
        slos.append({"id": f"ch{chapter:02d}-slo{number:02d}", "number": number, "text": text})

    result = ChapterSlos(
        chapter=chapter,
        title=info["title"],
        printed_page=info["printed_pages"][0],
        source="Typed by Izan from the physical book",
        slos=slos,
    )
    out = folder / "slos.json"
    out.write_text(json.dumps(result.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    data = convert(int(sys.argv[1]))
    print(f"Chapter {data.chapter}: {len(data.slos)} SLOs written to slos.json")
