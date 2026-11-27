"""Tests for the question validator (schema v2, ADR 0004), run against the real Chapter 1 data."""

import copy

import pytest

from validate_questions import Block, Context, check_bank, check_question, load_context, stem


@pytest.fixture(scope="module")
def ctx():
    return load_context(1)


# Exercise MCQ 5, book page 18 (answer from page 3).
EX_MCQ = {
    "id": "ch01-q001",
    "chapter": 1,
    "type": "mcq",
    "text": "Which structure of the plant transports sugar?",
    "options": ["Mesophyll cells", "Lower xylem", "Phloem", "Xylem"],
    "answer": "Phloem",
    "marks": 1,
    "slo_ids": ["S-07-A-02"],
    "cognitive_level": "Understanding",
    "source": "exercise",
    "question_page": 18,
    "answer_sources": [{"page": 3, "excerpt": "Phloem tissues conduct food throughout the"}],
}

# Exercise Short Q11, book page 19 (answer from key points, page 17).
EX_SHORT = {
    "id": "ch01-q002",
    "chapter": 1,
    "type": "short",
    "text": "What is the role of nitrates in plants?",
    "answer": "Nitrates are used by plants to produce protein.",
    "marks": 2,
    "slo_ids": ["S-07-A-04"],
    "cognitive_level": "Knowledge",
    "source": "exercise",
    "question_page": 19,
    "answer_sources": [{"page": 17, "excerpt": "nitrates are used by plants to produce protein."}],
}

# Exercise Long Q3, book page 19 (answer from page 15).
EX_LONG = {
    "id": "ch01-q003",
    "chapter": 1,
    "type": "long",
    "text": "Make a comparison between photosynthesis and respiration.",
    "answer": "Photosynthesis and respiration are complementary processes to each other. "
              "They maintain the oxygen-carbon dioxide balance in nature together.",
    "marks": 5,
    "slo_ids": ["S-07-A-06"],
    "cognitive_level": "Understanding",
    "source": "exercise",
    "question_page": 19,
    "answer_sources": [{"page": 15, "excerpt": "Photosynthesis and respiration are complementary processes to each other."}],
}

# A generated MCQ (needs its note).
GEN_MCQ = {
    "id": "ch01-q004",
    "chapter": 1,
    "type": "mcq",
    "text": "Which tissues conduct food throughout the plant?",
    "options": ["Xylem tissues", "Phloem tissues", "Dermal tissues", "Ground tissues"],
    "answer": "Phloem tissues",
    "marks": 1,
    "slo_ids": ["S-07-A-02"],
    "cognitive_level": "Understanding",
    "source": "generated",
    "generated_note": "(Newly generated - SLO S-07-A-02, extra MCQ)",
    "question_page": 3,
    "answer_sources": [{"page": 3, "excerpt": "Phloem tissues conduct food throughout the"}],
}


def changed(base, **updates):
    q = copy.deepcopy(base)
    q.update(updates)
    return q


@pytest.mark.parametrize("question", [EX_MCQ, EX_SHORT, EX_LONG, GEN_MCQ],
                         ids=["exercise-mcq", "exercise-short", "exercise-long", "generated-mcq"])
def test_good_questions_pass(ctx, question):
    assert check_question(question, ctx) == []


# --- words -----------------------------------------------------------------

def test_rejects_word_not_in_chapter_in_generated_question(ctx):
    problems = check_question(changed(GEN_MCQ, text="Which tissues carry enzymes in the plant?"), ctx)
    assert any("enzymes" in p for p in problems)


def test_rejects_outside_word_in_generated_distractor(ctx):
    q = changed(GEN_MCQ, options=["Xylem tissues", "Phloem tissues", "Dermal tissues", "Meristem tissues"])
    assert any("meristem" in p for p in check_question(q, ctx))


def test_rejects_outside_word_in_any_answer(ctx):
    problems = check_question(changed(EX_SHORT, answer="Nitrates make enzymes."), ctx)
    assert any("enzymes" in p for p in problems)


def test_exercise_mcq_keeps_the_book_options_as_printed(ctx):
    # "Vacoule" is the book's own spelling in exercise MCQ 7; it must be copied, not checked
    q = changed(EX_MCQ, text="In which organelle of the plant cell, process of respiration takes places?",
                options=["Nucleus", "Mitochondrion", "Chloroplast", "Vacoule"], answer="Mitochondrion",
                slo_ids=["S-07-A-06"], answer_sources=[{"page": 15, "excerpt": "Photosynthesis and respiration are complementary processes to each other."}])
    assert not any("words not in chapter" in p for p in check_question(q, ctx))


def test_cut_off_fragments_do_not_count_as_chapter_words(ctx):
    # "ntrally" only appears inside a [?ntrally] mark, so it must not be allowed
    assert not ctx.knows("ntrally")


def test_simple_word_endings_are_allowed(ctx):
    assert ctx.knows("leaves")
    assert ctx.knows("conducts")
    assert stem("cells") == stem("cell")


def test_base_form_of_a_chapter_word_is_allowed(ctx):
    for word in ("face", "diffuse", "remove", "stores"):
        assert ctx.knows(word), word
    assert not ctx.knows("enzyme")


def test_rejects_long_sentence_in_generated_question(ctx):
    long_q = "Which " + " and ".join(["tissues conduct food"] * 8) + "?"
    assert any("sentence too long" in p for p in check_question(changed(GEN_MCQ, text=long_q), ctx))


# --- exercise questions are copied exactly ---------------------------------

def test_rejects_exercise_text_not_in_the_book(ctx):
    problems = check_question(changed(EX_SHORT, text="What do nitrates do in plants?"), ctx)
    assert any("not found word for word in the exercise" in p for p in problems)


def test_rejects_exercise_text_on_wrong_page(ctx):
    problems = check_question(changed(EX_SHORT, question_page=18), ctx)
    assert any("not found word for word in the exercise" in p for p in problems)


def test_rejects_exercise_option_not_printed(ctx):
    q = changed(EX_MCQ, options=["Mesophyll cells", "Lower xylem", "Phloem", "Root hair"])
    assert any("options not printed" in p for p in check_question(q, ctx))


# --- SLO codes, levels and pages -------------------------------------------

def test_rejects_unknown_code(ctx):
    problems = check_question(changed(EX_SHORT, slo_ids=["S-07-A-42"]), ctx)
    assert any("SLO S-07-A-42" in p for p in problems)


def test_rejects_badly_written_code(ctx):
    assert any("not an SLO code" in p for p in check_question(changed(EX_SHORT, slo_ids=["ch01-slo04"]), ctx))


def test_level_must_be_the_first_codes_level(ctx):
    problems = check_question(changed(EX_SHORT, cognitive_level="Evaluate"), ctx)
    assert any("S-07-A-04 is Knowledge" in p for p in problems)


def test_question_with_two_codes_takes_the_first_codes_level(ctx):
    q = changed(EX_SHORT, slo_ids=["S-07-A-04", "S-07-A-03"])
    assert check_question(q, ctx) == []


def test_rejects_answer_page_not_taught_by_the_codes(ctx):
    # page 13 (photosynthesis) is not a page of S-07-A-04 (minerals)
    q = changed(EX_SHORT, answer_sources=[{"page": 13, "excerpt": "Glucose is the food of plants."}])
    assert any("not one of the pages" in p for p in check_question(q, ctx))


def test_rejects_generated_question_page_not_taught_by_its_code(ctx):
    assert any("question_page 13" in p for p in check_question(changed(GEN_MCQ, question_page=13), ctx))


def test_rejects_page_outside_chapter(ctx):
    assert any("outside the chapter" in p for p in check_question(changed(GEN_MCQ, question_page=25), ctx))


# --- answer sources --------------------------------------------------------

def test_rejects_fake_answer_excerpt(ctx):
    q = changed(EX_MCQ, answer_sources=[{"page": 3, "excerpt": "Plants eat soil every night."}])
    assert any("not found" in p for p in check_question(q, ctx))


def test_rejects_answer_excerpt_with_cut_off_text(ctx):
    q = changed(EX_MCQ, answer_sources=[{"page": 3, "excerpt": "Phloem tissues conduct food throughout the [pl?]"}])
    assert any("cut-off" in p for p in check_question(q, ctx))


def test_rejects_answer_from_exercise_text():
    mini = Context(
        chapter=1,
        code_pages={"S-07-A-02": {18}},
        code_level={"S-07-A-02": "Understanding"},
        page_range=(1, 19),
        blocks=[Block(18, "exercise", "5. Which structure of the plant transports sugar? a. Mesophyll cells b. Lower xylem c. Phloem d. Xylem")],
    )
    q = changed(EX_MCQ, answer_sources=[{"page": 18, "excerpt": "Which structure of the plant transports sugar?"}])
    assert any("exercise text" in p for p in check_question(q, mini))


def test_rejects_answer_without_source(ctx):
    assert any("answer_sources" in p for p in check_question(changed(EX_SHORT, answer_sources=[]), ctx))


# --- type and source rules (schema) ----------------------------------------

def test_rejects_true_false(ctx):
    assert any("type" in p for p in check_question(changed(EX_SHORT, type="true_false", marks=1), ctx))


def test_rejects_mcq_answer_not_in_options(ctx):
    assert any("answer must be one of the options" in p for p in check_question(changed(EX_MCQ, answer="Phloem tissues"), ctx))


def test_rejects_mcq_with_three_options(ctx):
    q = changed(EX_MCQ, options=["Mesophyll cells", "Lower xylem", "Phloem"])
    assert any("exactly 4 options" in p for p in check_question(q, ctx))


def test_rejects_short_question_with_options(ctx):
    assert any("must not have options" in p for p in check_question(changed(EX_SHORT, options=["a", "b", "c", "d"]), ctx))


@pytest.mark.parametrize("base,wrong", [(EX_MCQ, 2), (EX_SHORT, 1), (EX_LONG, 2)])
def test_rejects_wrong_marks_for_type(ctx, base, wrong):
    assert any("mark(s)" in p for p in check_question(changed(base, marks=wrong), ctx))


def test_rejects_note_on_exercise_question(ctx):
    q = changed(EX_SHORT, generated_note="(Newly generated - SLO S-07-A-04, extra MCQ)")
    assert any("must not have a generated_note" in p for p in check_question(q, ctx))


def test_rejects_generated_question_without_note(ctx):
    assert any("needs its generated_note" in p for p in check_question(changed(GEN_MCQ, generated_note=""), ctx))


def test_rejects_old_fields(ctx):
    assert any("slo_id" in p for p in check_question(changed(EX_SHORT, slo_id="ch01-slo04"), ctx))


def test_rejects_missing_figure_file(ctx):
    q = changed(EX_SHORT, figure="figures/ch01-does-not-exist.png")
    assert any("does not exist" in p for p in check_question(q, ctx))


# --- bank level: duplicates and coverage rules -----------------------------

def one_code_ctx(ctx):
    """Chapter 1 limited to S-07-A-02, so one exercise question covers every code."""
    return Context(chapter=1, code_pages={"S-07-A-02": ctx.code_pages["S-07-A-02"]},
                   code_level={"S-07-A-02": "Understanding"}, page_range=ctx.page_range,
                   blocks=ctx.blocks, common=ctx.common)


def test_rejects_duplicate_id_and_text(ctx):
    report = check_bank([EX_SHORT, changed(EX_MCQ, id=EX_SHORT["id"])], ctx)
    assert "duplicate id" in report["ch01-q002"]
    report = check_bank([EX_SHORT, changed(EX_SHORT, id="ch01-q009")], ctx)
    assert "duplicate question text" in report["ch01-q009"]


def test_all_covered_allows_one_extra_mcq_per_code(ctx):
    assert check_bank([EX_MCQ, GEN_MCQ], one_code_ctx(ctx)) == {}


def test_all_covered_rejects_a_second_extra_mcq_for_the_same_code(ctx):
    second = changed(GEN_MCQ, id="ch01-q005", text="Which tissues conduct water in the plant?",
                     answer_sources=[{"page": 3, "excerpt": "Xylem tissues conduct water and minerals"}])
    report = check_bank([EX_MCQ, GEN_MCQ, second], one_code_ctx(ctx))
    assert any("only 1 extra MCQ per code" in p for p in report["ch01-q005"])


def test_all_covered_rejects_generated_short(ctx):
    gen_short = changed(EX_SHORT, id="ch01-q005", source="generated", slo_ids=["S-07-A-02"],
                        cognitive_level="Understanding", text="What do phloem tissues conduct?",
                        answer="Phloem tissues conduct food.", question_page=3,
                        generated_note="(Newly generated - SLO S-07-A-02, extra MCQ)",
                        answer_sources=[{"page": 3, "excerpt": "Phloem tissues conduct food throughout the"}])
    report = check_bank([EX_MCQ, gen_short], one_code_ctx(ctx))
    assert any("only extra MCQs" in p for p in report["ch01-q005"])


def test_uncovered_code_needs_the_not_covered_note(ctx):
    # only S-07-A-04 is covered here, so S-07-A-02 is uncovered
    report = check_bank([EX_SHORT, GEN_MCQ], ctx)
    assert any("not covered in exercise" in p for p in report["ch01-q004"])
    fixed = changed(GEN_MCQ, generated_note="(Newly generated - SLO S-07-A-02, not covered in exercise)")
    assert check_bank([EX_SHORT, fixed], ctx) == {}


def test_rejects_generated_question_for_a_covered_code_when_others_are_uncovered(ctx):
    report = check_bank([EX_MCQ, changed(GEN_MCQ, generated_note="(Newly generated - SLO S-07-A-02, not covered in exercise)")], ctx)
    assert any("only for uncovered codes" in p for p in report["ch01-q004"])


def test_rejects_two_generated_questions_of_one_type_on_one_fact(ctx):
    note = "(Newly generated - SLO S-07-A-02, not covered in exercise)"
    first = changed(GEN_MCQ, generated_note=note)
    padded = changed(first, id="ch01-q005", text="Name the tissues that conduct food throughout the plant.")
    report = check_bank([EX_SHORT, first, padded], ctx)
    assert any("already uses this book fact" in p for p in report["ch01-q005"])
