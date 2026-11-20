# 3-day prototype plan – Class 7 Science test generator

Goal: demo where a teacher picks chapter, topic(s) and number of questions,
clicks Generate, and gets a print-ready PDF of random questions from a
reviewed question bank (Chapter 1 first).

Legend: **M** = must, **S** = should, **C** = cut unless ahead.
Owner is Claude unless marked "Izan". Status: todo / doing / done.

## Day 1 – book to clean data
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 0 | Install Node 22 + Python 3.12 | `node -v` shows v22, `python --version` shows 3.12 | M | done |
| 1 | Folder skeleton, .gitignore, PDF copied into `book/` (Izan copies) | `git status` does not show the PDF; skeleton pushed | M | done |
| 2 | Render all pages to images with PyMuPDF; record rotation per page and fix it | 196 images in `data/pages/`; every page checked upright | M | done |
| 3 | Map the book: chapter titles + page ranges, glossary range → `data/book.json` | 12 chapters + glossary listed; Izan confirms against the contents page | M | done |
| 4 | Izan types Chapter 1 SLOs → `data/ch01/slos.json` | File passes schema check; Izan says it matches the book | M (Izan) | done (9 SLOs) |
| 5 | Read Chapter 1 pages (Claude vision) → `data/ch01/text.json`: topics, text per page, UNREADABLE marks | Passes schema; Izan spot-checks 2 pages against the book | M | done (Izan checked pages 5 and 13) |
| 6 | ADR 0001: offline question bank, no runtime AI | File exists, under 1 page | S | todo |

Notes from task 2:
- Every PDF page is one book page scanned sideways: odd PDF pages turn 270°,
  even pages 90° (`data/page_rotations.json`). Re-create images with
  `.venv/Scripts/python.exe pipeline/render_pages.py --sheets`.
- Printed page number = PDF page − 3 (PDF page 4 = book page 1). To confirm in task 3.

Notes from task 5:
- Transcripts per page in `data/ch01/pages/bNNN.txt` (marks explained in its README);
  `pipeline/build_text.py 1` builds `data/ch01/text.json` (202 blocks, 8 topics).
- The scan cuts words at the page edges: 104 of 202 blocks contain `[?...]` marks.
  Questions must quote only clean stretches of text (validator rule in task 7).

## Day 2 – question bank, validator, app skeleton
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 7 | Question schema + validator (unknown words vs chapter text + `common_words.txt`, SLO exists, excerpt really in text, page in chapter range) | pytest passes, incl. tests that reject an outside word, fake SLO, fake excerpt | M | done (18 tests pass) |
| 8 | Add fill-blank + true/false to schema and validator | New tests pass | M | todo |
| 8a | Write Ch1 bank in batches of one topic at a time (~20 per topic) | Each batch passes validator; total 150+ | M | todo |
| 9 | Coverage report: questions per SLO / topic / type | Every SLO has 10+ questions | M | todo |
| 10a | Claude self-review: re-check every question against its quote (answer really in quote? simple, clear wording?); clear ones → `approved` with note "self-checked", doubtful ones → `pending` with a reason | Every question approved or flagged | M | todo |
| 10b | Izan spot-check: all flagged questions + 2 random approved per topic (~15 min) | Spot-check done; problems fixed or rejected | M (Izan) | todo |
| 10c | Simple review page: one question at a time with answer + book quote, Approve / Reject buttons, saves to questions.json | Izan can review a batch with clicks only | S | todo |
| 11 | Next.js app pickers (load from JSON): Class 7 → Science → Ch1; "Select by: Topics / SLOs" toggle; question type; count 10/15/20/25 | Works with the real bank; lint + typecheck pass | M | todo |
| 12 | Sampling with spread + count limits | Vitest passes: right count, no duplicates, spread across chosen topics/SLOs, only approved, larger counts disabled when pool too small | M | todo |
| - | Long-answer type | | C | cut |

### Question bank decisions (agreed with Izan, 2026-11-20)
- **Size:** about 150-180 questions for Chapter 1 (about 15-20 per SLO). Rule of thumb:
  the pool for a selection should be 3-4x the paper size, so two papers share only a few
  questions. Small topics (1.3, 1.6, 1.7, 1.8) can honestly support only about 10-20
  questions; no padding with reworded copies.
- **Types:** MCQ (1 mark), fill in the blank (1 mark), true/false (1 mark),
  short answer (2 marks). One book fact can give several types.
  Example (page 13): MCQ "What is the food of plants?"; fill-blank "______ is the food
  of plants."; true/false "Oxygen is the food of plants." (False); short "Name the food of plants."

### What the teacher sees
1. Class 7 → Science → Chapter 1.
2. "Select by: Topics | SLOs" toggle, then tick one or many (or "All").
3. Question type: MCQ / Fill in the blank / True-False / Short answer / Mixed.
4. Number of questions: 10 / 15 / 20 / 25. Counts larger than the available pool are
   disabled, with the message "Only N questions available for this selection".
5. Generate → print-ready PDF.

Sampling rules: no duplicates in one paper; spread across the chosen SLOs/topics
(round-robin); mixed papers use a fixed split (for example 25 = 10 MCQ + 5 fill-blank +
5 T/F + 5 short), grouped by type with section headings and marks; only `approved`
questions are used.

### Review approach
Izan does NOT read every question. The validator guarantees book-only words, real
quotes, real SLOs/pages; Claude self-reviews all (10a); Izan spot-checks flagged + a
random sample (10b, ~15 min). Accepted risk: a few awkward wordings may slip through,
never outside facts. Any question can be set to `rejected` later and the app stops
using it immediately. If behind: cut true/false first; keep MCQ + fill-blank + short.

## Day 3 – PDF, polish, rehearsal
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 13 | Print layout: school name, class, subject, date, marks beside each question, total marks | Generated PDF looks right on A4 print preview | M | todo |
| 14 | PDF download via Playwright (fallback: print CSS + browser "Save as PDF") | Click Generate → PDF downloads in < 5 s | M | todo |
| 15 | Optional answer key (separate page) | Toggle works; key matches the questions | S | todo |
| 16 | Mixed paper (all four types, grouped by type with section headings) | Mixed option works and is tested | C | todo |
| 17 | Loading / empty / error states, every control works | Manual check list passes | M | todo |
| 18 | Chapters 2-3 through tasks 4-10 | Bank for those chapters reviewed | C | todo |
| 19 | Demo script + rehearsal | Full demo run twice without problems | M | todo |

## Folder layout
```
book/            scanned PDF (git-ignored)
docs/            PLAN.md, adr/
pipeline/        Python: render pages, schemas, validator, tests
data/pages/      page images (git-ignored)
data/book.json   chapters + page ranges
data/chXX/       slos.json (typed by Izan), text.json, questions.json
web/             Next.js app
```

Question record: `id, chapter, topic, slo_id, type (mcq|fill_blank|true_false|short),
question, options[], answer, marks, page, source_excerpt, review_status, review_note`.
