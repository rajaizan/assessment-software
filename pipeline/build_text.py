"""Build data/chXX/text.json from the page transcripts in data/chXX/pages/bNNN.txt.

Usage: .venv/Scripts/python.exe pipeline/build_text.py 1
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from schemas import ChapterText

ROOT = Path(__file__).resolve().parent.parent
GAP = re.compile(r"\[[^\]]*\?[^\]]*\]|UNREADABLE")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def classify(line: str) -> tuple[str, str]:
    if line.startswith("## "):
        return "heading", line[3:].strip()
    if line.startswith("[FIG]"):
        return "figure", line[5:].strip()
    if line.startswith("[TABLE]"):
        return "table", line[7:].strip()
    if line.startswith("[BOX"):
        return "box", line
    if line.startswith("|"):
        return "table_row", line
    if line.startswith("- "):
        return "list_item", line[2:].strip()
    return "paragraph", line


# Headings that switch the part of the chapter (everything after them belongs to it).
PART_HEADINGS = {"Key Points": "key_points", "Exercise": "exercise"}


def build(chapter: int) -> ChapterText:
    folder = ROOT / "data" / f"ch{chapter:02d}"
    book = read_json(ROOT / "data" / "book.json")
    info = book["chapters"][chapter - 1]
    offset = book["printed_page_offset"]

    first, last = info["printed_pages"]
    part = "content"
    blocks = []
    for page in range(first, last + 1):
        path = folder / "pages" / f"b{page:03d}.txt"
        if not path.exists():
            raise SystemExit(f"Missing transcript {path.name}")
        n = 0
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line:
                continue
            kind, text = classify(line)
            if kind == "heading" and text in PART_HEADINGS:
                part = PART_HEADINGS[text]
            n += 1
            blocks.append({
                "id": f"ch{chapter:02d}-p{page:03d}-b{n:02d}",
                "printed_page": page,
                "pdf_page": page + offset,
                # the chapter's first page holds the title and the SLO list
                "part": "slo_list" if page == first else part,
                "kind": kind,
                "text": text,
                "has_gaps": bool(GAP.search(text)),
            })

    result = ChapterText(
        chapter=chapter,
        title=info["title"],
        source="Transcribed by Claude from page images; spot-checked by Izan",
        blocks=blocks,
    )
    out = folder / "text.json"
    out.write_text(json.dumps(result.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    data = build(int(sys.argv[1]))
    gaps = sum(b.has_gaps for b in data.blocks)
    print(f"Chapter {data.chapter}: {len(data.blocks)} blocks, {gaps} with gaps")
    for part in ("slo_list", "content", "key_points", "exercise"):
        pages = sorted({b.printed_page for b in data.blocks if b.part == part})
        count = sum(b.part == part for b in data.blocks)
        print(f"  {part:<10} {count:>3} blocks  pages {pages[0]}-{pages[-1]}" if pages else f"  {part}: none")
