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


def build(chapter: int) -> ChapterText:
    folder = ROOT / "data" / f"ch{chapter:02d}"
    book = read_json(ROOT / "data" / "book.json")
    info = book["chapters"][chapter - 1]
    offset = book["printed_page_offset"]
    topic_cfg = read_json(folder / "topics.json")
    starts = {t["match"]: t["id"] for t in topic_cfg["topics"]}
    ends = topic_cfg["end_markers"]

    first, last = info["printed_pages"]
    section = "intro"
    blocks, topic_pages = [], {}
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
            if kind == "heading":
                if text in starts:
                    section = starts[text]
                elif text in ends:
                    section = ends[text]
            n += 1
            blocks.append({
                "id": f"ch{chapter:02d}-p{page:03d}-b{n:02d}",
                "printed_page": page,
                "pdf_page": page + offset,
                "section": section,
                "kind": kind,
                "text": text,
                "has_gaps": bool(GAP.search(text)),
            })
            if section in starts.values():
                pages = topic_pages.setdefault(section, [page, page])
                pages[1] = page

    missing = [m for m, tid in starts.items() if tid not in topic_pages]
    if missing:
        raise SystemExit(f"Topic headings not found in transcripts: {missing}")

    result = ChapterText(
        chapter=chapter,
        title=info["title"],
        source="Transcribed by Claude from page images; spot-checked by Izan",
        topics=[{"id": t["id"], "title": t["title"], "printed_pages": topic_pages[t["id"]]}
                for t in topic_cfg["topics"]],
        blocks=blocks,
    )
    out = folder / "text.json"
    out.write_text(json.dumps(result.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    data = build(int(sys.argv[1]))
    gaps = sum(b.has_gaps for b in data.blocks)
    print(f"Chapter {data.chapter}: {len(data.blocks)} blocks, {gaps} with gaps, {len(data.topics)} topics")
    for t in data.topics:
        n = sum(b.section == t.id for b in data.blocks)
        print(f"  {t.id} {t.title}  pages {t.printed_pages[0]}-{t.printed_pages[1]}  ({n} blocks)")
