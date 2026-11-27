"""Tests for copying the chapter exercise (task 1.3)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from extract_exercise import extract, parse_item, section_type
from schemas import ChapterExercise, ExerciseItem
from validate_questions import load_context, normalize

DATA = Path(__file__).resolve().parents[2] / "data"
WEB = Path(__file__).resolve().parents[2] / "web" / "public"


def block(text, kind="list_item", page=18):
    return {"part": "exercise", "kind": kind, "text": text, "printed_page": page}


def test_parse_mcq_with_full_stops_inside_options():
    text, options = parse_item("8. The importance of respiration in plants is that: a. it provides oxygen to plants. "
                               "b. it provides energy. c. it releases carbon dioxide. d. all of the above", "mcq", 8)
    assert text == "The importance of respiration in plants is that:"
    assert options == ["it provides oxygen to plants.", "it provides energy.", "it releases carbon dioxide.", "all of the above"]


def test_parse_short_keeps_its_parts_as_printed():
    text, options = parse_item("7. a. Define translocation. b. Enlist the cells.", "short", 7)
    assert text == "a. Define translocation. b. Enlist the cells."
    assert options == []


def test_cut_off_number_uses_the_position():
    assert parse_item("[?2.] Why is the photosynthesis important?", "short", 12)[0] == "Why is the photosynthesis important?"


def test_wrong_printed_number_stops():
    with pytest.raises(SystemExit):
        parse_item("5. Why?", "short", 6)


def test_mcq_without_four_options_stops():
    with pytest.raises(SystemExit):
        parse_item("1. Which? a. One b. Two", "mcq", 1)


def test_unknown_section_heading_stops():
    with pytest.raises(SystemExit):
        section_type("Fill in the blanks.")


def test_sections_restart_numbering():
    blocks = [block("A Choose the correct option.", "heading"), block("1. Which? a. w b. x c. y d. z"),
              block("B Answer briefly.", "heading"), block("1. Why is it so?"), block("2. How does it work?")]
    ids = [item.id for item in extract(1, blocks).items]
    assert ids == ["ch01-ex-a01", "ch01-ex-b01", "ch01-ex-b02"]


def test_cut_off_text_is_rejected():
    with pytest.raises(ValidationError, match="read from the book"):
        ExerciseItem(id="ch01-ex-a10", section="A", number=10, type="mcq", text="If there would be no [photosynthesi?]",
                     options=["Nitrogen", "Carbon dioxide", "Oxygen", "Hydrogen"], question_page=18)


def test_chapter_1_exercise_is_complete_and_exact():
    exercise = ChapterExercise(**json.loads((DATA / "ch01" / "exercise.json").read_text(encoding="utf-8")))
    counts = {k: sum(i.type == k for i in exercise.items) for k in ("mcq", "short", "long")}
    assert counts == {"mcq": 12, "short": 12, "long": 4}
    printed = load_context(1).blocks
    for item in exercise.items:
        page = [normalize(b.text) for b in printed if b.page == item.question_page and b.part == "exercise"]
        assert any(normalize(item.text) in b and all(o in b for o in item.options) for b in page), item.id


def test_chapter_1_short_5_has_its_picture():
    exercise = ChapterExercise(**json.loads((DATA / "ch01" / "exercise.json").read_text(encoding="utf-8")))
    with_figure = {i.id: i.figure for i in exercise.items if i.figure}
    assert with_figure == {"ch01-ex-b05": "figures/ch01-short05.png"}
    assert (WEB / "figures" / "ch01-short05.png").is_file()
