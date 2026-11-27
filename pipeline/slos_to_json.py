"""Build a checked data/chXX/slos.json from:
  - data/chXX/slos.txt        typed by Izan: SLO statement from the physical book, then
                              "| code | level" from the client's coded SLO list
  - data/chXX/slo_pages.json  printed pages that teach each SLO (proposed by Claude,
                              confirmed by Izan)
  - data/levels.json          allowed cognitive levels and their groups

Usage: .venv/Scripts/python.exe pipeline/slos_to_json.py 1
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from schemas import ChapterSlos, LevelGroups

ROOT = Path(__file__).resolve().parent.parent
LINE = re.compile(r"^(\d+)\.\s+(.+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*$")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_line(line: str) -> tuple[int, str, str, str]:
    """'N. statement | code | level' -> (number, statement, code, level)."""
    match = LINE.match(line)
    if not match:
        raise SystemExit(f"Line is not 'N. statement | code | level': {line!r}")
    number, text, code, level = match.groups()
    return int(number), re.sub(r"\s+", " ", text).strip(), code, level


def convert(chapter: int) -> ChapterSlos:
    folder = ROOT / "data" / f"ch{chapter:02d}"
    info = read_json(ROOT / "data" / "book.json")["chapters"][chapter - 1]
    page_map = read_json(folder / "slo_pages.json")
    first, last = info["printed_pages"]

    slos = []
    for raw in (folder / "slos.txt").read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        number, text, code, level = parse_line(line)
        slo_id = f"ch{chapter:02d}-slo{number:02d}"
        if slo_id not in page_map["pages"]:
            raise SystemExit(f"{slo_id} has no entry in slo_pages.json")
        pages = page_map["pages"][slo_id]["pages"]
        outside = [p for p in pages if not first <= p <= last]
        if outside:
            raise SystemExit(f"{slo_id}: pages {outside} are outside the chapter ({first}-{last})")
        slos.append({"id": slo_id, "number": number, "text": text,
                     "code": code, "level": level, "pages": pages})

    extra = set(page_map["pages"]) - {s["id"] for s in slos}
    if extra:
        raise SystemExit(f"slo_pages.json lists unknown SLOs: {sorted(extra)}")

    result = ChapterSlos(
        chapter=chapter,
        title=info["title"],
        printed_page=first,
        source="Statements typed by Izan from the physical book; codes and levels from the client's coded SLO list",
        pages_status=page_map["status"],
        slos=slos,
    )
    unknown = result.unknown_levels(LevelGroups(**read_json(ROOT / "data" / "levels.json")))
    if unknown:
        raise SystemExit(f"Levels not in data/levels.json: {unknown}")
    out = folder / "slos.json"
    out.write_text(json.dumps(result.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    data = convert(int(sys.argv[1]))
    print(f"Chapter {data.chapter}: {len(data.slos)} SLOs written to slos.json (pages {data.pages_status})")
