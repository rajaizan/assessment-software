"""Tests for the question validator, run against the real Chapter 1 data (SLO-only, ADR 0002)."""

import copy

import pytest

from validate_questions import Block, Context, check_bank, check_question, load_context, stem


@pytest.fixture(scope="module")
def ctx():
    return load_context(1)


GOOD_SHORT = {
    "id": "ch01-q001",
    "chapter": 1,
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
    "slo_id": "ch01-slo02",
    "type": "mcq",
    "question": "Which tissues conduct food throughout the plant?",
    "options": ["Xylem tissues", "Phloem tissues", "Dermal tissues", "Ground tissues"],
    "answer": "Phloem tissues",
    "marks": 1,
    "page": 3,
    "source_excerpt": "Phloem tissues conduct food throughout the",
}

GOOD_TF = {
    "id": "ch01-q003",
    "chapter": 1,
    "slo_id": "ch01-slo03",
    "type": "true_false",
    "question": "Oxygen is the food of plants.",
    "answer": "False",
    "marks": 1,
    "page": 13,
    "source_excerpt": "Glucose is the food of plants.",
}


def changed(base, **updates):
    q = copy.deepcopy(base)
    q.update(updates)
    return q


@pytest.mark.parametrize("question", [GOOD_SHORT, GOOD_MCQ, GOOD_TF], ids=["short", "mcq", "true_false"])
def test_good_questions_pass(ctx, question):
    assert check_question(question, ctx) == []


# --- words -----------------------------------------------------------------

def test_rejects_word_not_in_chapter(ctx):
    problems = check_question(changed(GOOD_SHORT, question="What food do enzymes make in plants?"), ctx)
    assert any("enzymes" in p for p in problems)


def test_rejects_outside_word_in_mcq_distractor(ctx):
    q = changed(GOOD_MCQ, options=["Xylem tissues", "Phloem tissues", "Dermal tissues", "Meristem tissues"])
    assert any("meristem" in p for p in check_question(q, ctx))


def test_cut_off_fragments_do_not_count_as_chapter_words(ctx):
    # "ntrally" only appears inside a [?ntrally] mark, so it must not be allowed
    assert not ctx.knows("ntrally")


def test_simple_word_endings_are_allowed(ctx):
    assert ctx.knows("leaves")
    assert ctx.knows("conducts")
    assert stem("cells") == stem("cell")


def test_rejects_long_sentence(ctx):
    long_q = "What is " + " and ".join(["the food of plants"] * 8) + "?"
    assert any("sentence too long" in p for p in check_question(changed(GOOD_SHORT, question=long_q), ctx))


# --- SLO and page links ----------------------------------------------------

def test_rejects_fake_slo(ctx):
    problems = check_question(changed(GOOD_SHORT, slo_id="ch01-slo42"), ctx)
    assert any("SLO ch01-slo42" in p for p in problems)


def test_rejects_page_not_taught_by_the_slo(ctx):
    # page 13 (photosynthesis) is not one of SLO 4's pages (minerals)
    problems = check_question(changed(GOOD_SHORT, slo_id="ch01-slo04"), ctx)
    assert any("not one of ch01-slo04's pages" in p for p in problems)


def test_rejects_page_outside_chapter(ctx):
    assert any("outside the chapter" in p for p in check_question(changed(GOOD_SHORT, page=25), ctx))


# --- source excerpt --------------------------------------------------------

def test_rejects_fake_excerpt(ctx):
    problems = check_question(changed(GOOD_SHORT, source_excerpt="Plants eat soil every night."), ctx)
    assert any("not found" in p for p in problems)


def test_rejects_excerpt_on_wrong_page(ctx):
    problems = check_question(changed(GOOD_SHORT, page=17), ctx)
    assert any("not found" in p for p in problems)


def test_rejects_excerpt_with_cut_off_text(ctx):
    q = changed(GOOD_MCQ, source_excerpt="Phloem tissues conduct food throughout the [pl?]")
    assert any("cut-off" in p for p in check_question(q, ctx))


def test_rejects_excerpt_from_exercise_text():
    mini = Context(
        chapter=1,
        slo_pages={"ch01-slo02": {18}},
        page_range=(1, 19),
        blocks=[Block(18, "exercise", "Which structure of the plant transports sugar?")],
    )
    q = changed(GOOD_SHORT, slo_id="ch01-slo02", page=18,
                question="Which structure of the plant transports sugar?",
                answer="Which structure of the plant transports sugar?",
                source_excerpt="Which structure of the plant transports sugar?")
    assert any("exercise text" in p for p in check_question(q, mini))


# --- type rules (schema) ---------------------------------------------------

def test_rejects_mcq_answer_not_in_options(ctx):
    problems = check_question(changed(GOOD_MCQ, answer="Phloem"), ctx)
    assert any("answer must be one of the options" in p for p in problems)


def test_rejects_mcq_with_three_options(ctx):
    problems = check_question(changed(GOOD_MCQ, options=["Xylem tissues", "Phloem tissues", "Dermal tissues"]), ctx)
    assert any("exactly 4 options" in p for p in problems)


def test_rejects_short_question_with_options(ctx):
    problems = check_question(changed(GOOD_SHORT, options=["a", "b", "c", "d"]), ctx)
    assert any("must not have options" in p for p in problems)


def test_rejects_true_false_with_options(ctx):
    problems = check_question(changed(GOOD_TF, options=["True", "False", "Maybe", "None"]), ctx)
    assert any("must not have options" in p for p in problems)


def test_rejects_true_false_answer_other_than_true_or_false(ctx):
    problems = check_question(changed(GOOD_TF, answer="No"), ctx)
    assert any("'True' or 'False'" in p for p in problems)


def test_rejects_wrong_marks_for_type(ctx):
    problems = check_question(changed(GOOD_SHORT, marks=1), ctx)
    assert any("worth 2 mark" in p for p in problems)


def test_rejects_old_topic_field(ctx):
    problems = check_question(changed(GOOD_SHORT, topic="1.5"), ctx)
    assert any("topic" in p for p in problems)


# --- bank level ------------------------------------------------------------

def test_rejects_duplicate_id_and_text(ctx):
    report = check_bank([GOOD_SHORT, changed(GOOD_SHORT, question="Name the food of plants.",
                                             source_excerpt="Glucose is the food of plants")], ctx)
    assert "duplicate id" in report["ch01-q001"]
    report = check_bank([GOOD_SHORT, changed(GOOD_SHORT, id="ch01-q009",
                                             source_excerpt="Glucose is the food of plants")], ctx)
    assert "duplicate question text" in report["ch01-q009"]


def test_rejects_second_question_of_same_type_on_same_fact(ctx):
    padded = changed(GOOD_SHORT, id="ch01-q009", question="Name the food of plants.")
    report = check_bank([GOOD_SHORT, padded], ctx)
    assert any("same type already uses this source_excerpt" in p for p in report["ch01-q009"])


def test_allows_same_fact_for_different_types(ctx):
    assert check_bank([GOOD_SHORT, GOOD_TF], ctx) == {}
