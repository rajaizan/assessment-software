"""Tests for SLO codes, cognitive levels and level groups (task 1.1)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas import ChapterSlos, LevelGroups
from slos_to_json import parse_line

DATA = Path(__file__).resolve().parents[2] / "data"


def levels() -> LevelGroups:
    return LevelGroups(**json.loads((DATA / "levels.json").read_text(encoding="utf-8")))


def slo(number: int, code: str, level: str) -> dict:
    return {"id": f"ch01-slo{number:02d}", "number": number, "text": "A statement from the book.",
            "code": code, "level": level, "pages": [2]}


def chapter(*slos: dict) -> dict:
    return {"chapter": 1, "title": "Plant System", "printed_page": 1, "source": "test",
            "pages_status": "confirmed", "slos": list(slos)}


def test_parse_line_reads_code_and_level():
    assert parse_line("6. Describe  respiration. | S-07-A-06 | Understanding") == (
        6, "Describe respiration.", "S-07-A-06", "Understanding")


def test_parse_line_without_code_and_level_stops():
    with pytest.raises(SystemExit):
        parse_line("6. Describe respiration.")


def test_level_groups_match_the_client():
    groups = levels()
    assert groups.group_of("Knowledge") == "lower"
    assert groups.group_of("Understanding") == "middle"
    for name in ("Application", "Analysis", "Evaluate"):
        assert groups.group_of(name) == "higher"
    assert groups.group_of("Remember") is None


def test_level_in_two_groups_is_rejected():
    with pytest.raises(ValidationError):
        LevelGroups(source="t", groups={"lower": ["Knowledge"], "middle": ["Knowledge"], "higher": ["Evaluate"]})


def test_bad_code_is_rejected():
    with pytest.raises(ValidationError):
        ChapterSlos(**chapter(slo(1, "S7A1", "Knowledge")))


def test_one_code_may_cover_two_book_slos():
    data = ChapterSlos(**chapter(slo(1, "S-07-A-06", "Understanding"), slo(2, "S-07-A-06", "Understanding")))
    assert {s.code for s in data.slos} == {"S-07-A-06"}


def test_shared_code_with_two_levels_is_rejected():
    with pytest.raises(ValidationError, match="two different levels"):
        ChapterSlos(**chapter(slo(1, "S-07-A-06", "Understanding"), slo(2, "S-07-A-06", "Knowledge")))


def test_unknown_level_is_reported():
    data = ChapterSlos(**chapter(slo(1, "S-07-A-01", "Evaluat")))
    assert data.unknown_levels(levels()) == ["Evaluat"]


def test_chapter_1_has_9_book_slos_and_8_codes():
    data = ChapterSlos(**json.loads((DATA / "ch01" / "slos.json").read_text(encoding="utf-8")))
    assert len(data.slos) == 9
    assert sorted({s.code for s in data.slos}) == [f"S-07-A-0{n}" for n in range(1, 9)]
    assert data.unknown_levels(levels()) == []
