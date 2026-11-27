"""Tests for the exercise → SLO mapping check and coverage report (task 1.4)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from coverage_report import check, report
from schemas import ChapterExercise, ChapterMapping, ChapterSlos, MappingEntry

DATA = Path(__file__).resolve().parents[2] / "data" / "ch01"


def load(name, model):
    return model(**json.loads((DATA / name).read_text(encoding="utf-8")))


@pytest.fixture(scope="module")
def real():
    return load("exercise.json", ChapterExercise), load("mapping.json", ChapterMapping), load("slos.json", ChapterSlos)


def test_chapter_1_mapping_has_no_problems(real):
    assert check(*real).problems == []


def test_chapter_1_every_code_is_covered(real):
    cov = check(*real)
    assert cov.uncovered == []
    assert all(sum(e["counts"].values()) >= 1 for e in cov.codes.values())


def test_unmapped_item_is_reported(real):
    exercise, mapping, slos = real
    smaller = mapping.model_copy(update={"items": {k: v for k, v in mapping.items.items() if k != "ch01-ex-b08"}})
    assert "ch01-ex-b08 has no mapping" in check(exercise, smaller, slos).problems


def test_unknown_code_is_reported(real):
    exercise, mapping, slos = real
    items = dict(mapping.items, **{"ch01-ex-a01": MappingEntry(slo_ids=["S-07-A-99"], pages=[15], reason="test reason")})
    problems = check(exercise, mapping.model_copy(update={"items": items}), slos).problems
    assert any("unknown code" in p for p in problems)


def test_page_not_taught_by_the_code_is_reported(real):
    exercise, mapping, slos = real
    items = dict(mapping.items, **{"ch01-ex-a12": MappingEntry(slo_ids=["S-07-A-04"], pages=[5], reason="test reason")})
    problems = check(exercise, mapping.model_copy(update={"items": items}), slos).problems
    assert any("ch01-ex-a12: page(s) [5]" in p for p in problems)


def test_uncovered_code_is_found_and_reported(real):
    exercise, mapping, slos = real
    # move B04 (the only question for S-07-A-08) to S-07-A-07 only
    items = dict(mapping.items, **{"ch01-ex-b04": MappingEntry(slo_ids=["S-07-A-07"], pages=[10], reason="test reason")})
    changed = mapping.model_copy(update={"items": items})
    cov = check(exercise, changed, slos)
    assert cov.uncovered == ["S-07-A-08"]
    assert "only for these codes" in report(1, exercise, changed, cov)


def test_repeated_code_in_one_entry_is_rejected():
    with pytest.raises(ValidationError):
        MappingEntry(slo_ids=["S-07-A-01", "S-07-A-01"], pages=[2], reason="test reason")
