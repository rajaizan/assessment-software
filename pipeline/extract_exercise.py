"""Copy the chapter's own exercise out of text.json into data/chXX/exercise.json,
and cut the figures that exercise questions need into web/public/figures/.

Usage: .venv/Scripts/python.exe pipeline/extract_exercise.py 1

Inputs (all data, no chapter-specific code):
  - data/chXX/text.json      exercise blocks (part = "exercise"), transcribed from the book
  - data/chXX/figures.json   optional: page image + pixel box for each figure an item shows
  - data/pages/pNNN.png      page images (git-ignored), only needed when figures.json exists

Section headings decide the type: "Choose the correct option" → mcq,
"... briefly" → short, "... in detail" → long. An unknown heading stops the script.
Numbers come from the order inside each section; a readable printed number must match.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from schemas import ChapterExercise, FigureCrop

ROOT = Path(__file__).resolve().parent.parent
SECTION = re.compile(r"^([A-Z])\s+(.+)$")
SECTION_TYPES = (("choose the correct option", "mcq"), ("briefly", "short"), ("in detail", "long"))
NUMBER = re.compile(r"^(?:(\d+)\.|\[\?[^\]]*\])\s+")  # "5. " or a cut-off number like "[?2.] "
MCQ = re.compile(r"^(.*?)\s+a\.\s+(.+?)\s+b\.\s+(.+?)\s+c\.\s+(.+?)\s+d\.\s+(.+)$")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def section_type(heading: str) -> str:
    lower = heading.lower()
    for key, kind in SECTION_TYPES:
        if key in lower:
            return kind
    raise SystemExit(f"Unknown exercise section heading: {heading!r} (add it to SECTION_TYPES)")


def parse_item(text: str, kind: str, expected_number: int) -> tuple[str, list[str]]:
    """'5. Question? a. w b. x c. y d. z' -> ('Question?', ['w', 'x', 'y', 'z'])."""
    match = NUMBER.match(text)
    if not match:
        raise SystemExit(f"Exercise item does not start with a number: {text!r}")
    if match.group(1) and int(match.group(1)) != expected_number:
        raise SystemExit(f"Printed number {match.group(1)} but expected {expected_number}: {text!r}")
    rest = text[match.end():].strip()
    if kind != "mcq":
        return rest, []
    mcq = MCQ.match(rest)
    if not mcq:
        raise SystemExit(f"MCQ does not have options a. b. c. d.: {text!r}")
    return mcq.group(1).strip(), [o.strip() for o in mcq.groups()[1:]]


def extract(chapter: int, blocks: list[dict]) -> ChapterExercise:
    items = []
    section = kind = None
    count = 0
    for block in blocks:
        if block["part"] != "exercise":
            continue
        if block["kind"] == "heading":
            match = SECTION.match(block["text"])
            if match:
                section, kind, count = match.group(1), section_type(match.group(2)), 0
            continue
        if section is None:
            raise SystemExit(f"Exercise text before any section heading: {block['text']!r}")
        count += 1
        text, options = parse_item(block["text"], kind, count)
        items.append({
            "id": f"ch{chapter:02d}-ex-{section.lower()}{count:02d}",
            "section": section,
            "number": count,
            "type": kind,
            "text": text,
            "options": options,
            "question_page": block["printed_page"],
        })
    return ChapterExercise(chapter=chapter, source="Copied from the chapter exercise in text.json", items=items)


def add_figures(exercise: ChapterExercise, folder: Path) -> list[FigureCrop]:
    path = folder / "figures.json"
    if not path.exists():
        return []
    crops = [FigureCrop(**f) for f in read_json(path)["figures"]]
    by_id = {item.id: item for item in exercise.items}
    for crop in crops:
        if crop.item not in by_id:
            raise SystemExit(f"figures.json: unknown exercise item {crop.item}")
        by_id[crop.item].figure = crop.file
    return crops


def cut_figures(crops: list[FigureCrop]) -> None:
    from PIL import Image  # only needed when a chapter has figures

    for crop in crops:
        source = ROOT / "data" / "pages" / f"p{crop.pdf_page:03d}.png"
        target = ROOT / "web" / "public" / crop.file
        target.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            image.crop(crop.box).save(target, optimize=True)


def main() -> None:
    chapter = int(sys.argv[1])
    folder = ROOT / "data" / f"ch{chapter:02d}"
    exercise = extract(chapter, read_json(folder / "text.json")["blocks"])
    crops = add_figures(exercise, folder)
    cut_figures(crops)
    exercise = ChapterExercise.model_validate(exercise.model_dump())  # re-check after adding figures
    out = folder / "exercise.json"
    out.write_text(json.dumps(exercise.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    kinds = {k: sum(i.type == k for i in exercise.items) for k in ("mcq", "short", "long")}
    print(f"Chapter {chapter}: {len(exercise.items)} exercise items {kinds}, {len(crops)} figure(s) -> exercise.json")


if __name__ == "__main__":
    main()
