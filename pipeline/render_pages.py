"""Render every page of the book PDF to a PNG image.

Usage (from the project root):
    .venv/Scripts/python.exe pipeline/render_pages.py
    .venv/Scripts/python.exe pipeline/render_pages.py --sheets   # also make preview sheets

Rotation fixes are read from data/page_rotations.json, e.g. {"17": 90, "18": 270}
(keys = 1-based PDF page index, values = clockwise degrees to turn the page).
Output: data/pages/p001.png ... (git-ignored, can always be re-created).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BOOK_DIR = ROOT / "book"
PAGES_DIR = ROOT / "data" / "pages"
SHEETS_DIR = PAGES_DIR / "sheets"
ROTATIONS_FILE = ROOT / "data" / "page_rotations.json"

DPI = 200
SHEET_COLS, SHEET_ROWS = 5, 4
THUMB_W, THUMB_H = 300, 400


def find_pdf() -> Path:
    pdfs = sorted(BOOK_DIR.glob("*.pdf"))
    if len(pdfs) != 1:
        raise SystemExit(f"Expected exactly one PDF in {BOOK_DIR}, found {len(pdfs)}")
    return pdfs[0]


def load_rotations() -> dict[int, int]:
    if not ROTATIONS_FILE.exists():
        return {}
    raw = json.loads(ROTATIONS_FILE.read_text(encoding="utf-8-sig"))
    rotations: dict[int, int] = {}
    for key, value in raw.items():
        if value not in (0, 90, 180, 270):
            raise SystemExit(f"Bad rotation {value} for page {key}; use 0/90/180/270")
        rotations[int(key)] = value
    return rotations


def page_path(index: int) -> Path:
    return PAGES_DIR / f"p{index:03d}.png"


def render_all(pdf: Path, rotations: dict[int, int]) -> int:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=DPI)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        turn = rotations.get(i, 0)
        if turn:
            img = img.rotate(-turn, expand=True)  # PIL rotates counter-clockwise
        img.save(page_path(i), optimize=True)
    return doc.page_count


def make_sheets(page_count: int) -> None:
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    per_sheet = SHEET_COLS * SHEET_ROWS
    label_h = 24
    for start in range(1, page_count + 1, per_sheet):
        sheet = Image.new("RGB", (SHEET_COLS * THUMB_W, SHEET_ROWS * (THUMB_H + label_h)), "white")
        draw = ImageDraw.Draw(sheet)
        for slot, index in enumerate(range(start, min(start + per_sheet, page_count + 1))):
            thumb = Image.open(page_path(index))
            thumb.thumbnail((THUMB_W - 10, THUMB_H - 10))
            x = (slot % SHEET_COLS) * THUMB_W
            y = (slot // SHEET_COLS) * (THUMB_H + label_h)
            draw.text((x + 5, y + 4), f"PDF page {index}", fill="red")
            sheet.paste(thumb, (x + 5, y + label_h))
        end = min(start + per_sheet - 1, page_count)
        sheet.save(SHEETS_DIR / f"sheet_{start:03d}-{end:03d}.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheets", action="store_true", help="also make preview sheets")
    args = parser.parse_args()

    count = render_all(find_pdf(), load_rotations())
    print(f"Rendered {count} pages to {PAGES_DIR}")
    if args.sheets:
        make_sheets(count)
        print(f"Preview sheets in {SHEETS_DIR}")


if __name__ == "__main__":
    main()
