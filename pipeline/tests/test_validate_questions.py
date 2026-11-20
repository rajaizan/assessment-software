"""Tests for the question validator, run against the real Chapter 1 data."""

import copy

import pytest

from validate_questions import check_bank, check_question, load_context, stem


@pytest.fixture(scope="module")
def ctx():
    return load_context(1)


GOOD_SHORT = {
    "id": "ch01-q001",
    "chapter": 1,
    "topic": "1.5",
    "slo_id": "ch01-slo03",
    "type": "short",
    "question": "What is the food of plants?",
    "answer": "Glucose is the food of plants.",
    "marks": 2,
    "page": 13,
    "source_excerpt": "Glucose is the food of plants.",
}

GOOD_MCQ = {
    "id": "ch01-q002",
    "chapter": 1,
    "topic": "1.1",
    "slo_id": "ch01-slo02",
    "type": "mcq",
    "question": "Which tissues conduct food throughout the plant?",
    "options": ["Xylem tissues", "Phloem tissues", "Dermal tissues", "Ground tissues"],
    "answer": "Phloem tissues",
    "marks": 1,
    "page": 3,
    "source_excerpt": "Phloem tissues conduct food throughout the",
}


def changed(base, **updates):
    q = copy.deepcopy(base)
    q.update(updates)
    return q


def test_good_short_question_passes(ctx):
    assert check_question(GOOD_SHORT, ctx) == []


def test_good_mcq_passes(ctx):
    assert check_question(GOOD_MCQ, ctx) == []


def test_rejects_word_not_in_chapter(ctx):
    q = changed(GOOD_SHORT, question="What food do enzymes make in plants?")
    problems = check_question(q, ctx)
    assert any("enzymes" in p for p in problems)


def test_rejects_outside_word_in_mcq_distractor(ctx):
    q = changed(GOOD_MCQ, options=["Xylem tissues", "Phloem tissues", "Dermal tissues", "Meristem tissues"])
    problems = check_question(q, ctx)
    assert any("meristem" in p for p in problems)


def test_rejects_fake_slo(ctx):
    problems = check_question(changed(GOOD_SHORT, slo_id="ch01-slo42"), ctx)
    assert any("SLO ch01-slo42" in p for p in problems)


def test_rejects_fake_topic(ctx):
    problems = check_question(changed(GOOD_SHORT, topic="1.9"), ctx)
    assert any("topic 1.9" in p for p in problems)


def test_rejects_fake_excerpt(ctx):
    problems = check_question(changed(GOOD_SHORT, source_excerpt="Plants eat soil every night."), ctx)
    assert any("not found" in p for p in problems)


def test_rejects_excerpt_on_wrong_page(ctx):
    problems = check_question(changed(GOOD_SHORT, page=14), ctx)
    assert any("not found" in p for p in problems)


def test_rejects_excerpt_with_cut_off_text(ctx):
    q = changed(GOOD_MCQ, source_excerpt="Phloem tissues conduct food throughout the [pl?]")
    problems = check_question(q, ctx)
    assert any("cut-off" in p for p in problems)


def test_rejects_excerpt_from_other_topic(ctx):
    problems = check_question(changed(GOOD_MCQ, topic="1.2"), ctx)
    assert any("not inside topic 1.2" in p for p in problems)


def test_rejects_page_outside_chapter(ctx):
    problems = check_question(changed(GOOD_SHORT, page=25), ctx)
    assert any("outside the chapter" in p for p in problems)


def test_rejects_mcq_answer_not_in_options(ctx):
    problems = check_question(changed(GOOD_MCQ, answer="Phloem"), ctx)
    assert any("answer must be one of the options" in p for p in problems)


def test_rejects_mcq_with_three_options(ctx):
    problems = check_question(changed(GOOD_MCQ, options=["Xylem tissues", "Phloem tissues", "Dermal tissues"]), ctx)
    assert any("exactly 4 options" in p for p in problems)


def test_rejects_short_question_with_options(ctx):
    problems = check_question(changed(GOOD_SHORT, options=["a", "b", "c", "d"]), ctx)
    assert any("must not have options" in p for p in problems)


def test_rejects_long_sentence(ctx):
    long_q = "What is " + " and ".join(["the food of plants"] * 8) + "?"
    problems = check_question(changed(GOOD_SHORT, question=long_q), ctx)
    assert any("sentence too long" in p for p in problems)


def test_rejects_duplicates_in_bank(ctx):
    report = check_bank([GOOD_SHORT, changed(GOOD_SHORT, question="Name the food of plants.")], ctx)
    assert "duplicate id" in report["ch01-q001"]
    report = check_bank([GOOD_SHORT, changed(GOOD_SHORT, id="ch01-q009")], ctx)
    assert "duplicate question text" in report["ch01-q009"]


def test_cut_off_fragments_do_not_count_as_chapter_words(ctx):
    # "ntrally" only appears inside a [?ntrally] mark, so it must not be allowed
    assert not ctx.knows("ntrally")


def test_simple_word_endings_are_allowed(ctx):
    assert ctx.knows("leaves")
    assert ctx.knows("conducts")
    assert stem("cells") == stem("cell")
