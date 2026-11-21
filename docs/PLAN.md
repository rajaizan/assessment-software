# 3-day prototype plan – Class 7 Science test generator

Goal: demo where a teacher picks class, subject, chapter, one or more **SLOs**,
the number of questions and the question type, clicks Generate, and gets a
print-ready paper of random questions from a reviewed question bank (Chapter 1 first).

Legend: **M** = must, **S** = should, **C** = cut unless ahead.
Owner is Claude unless marked "Izan". Status: todo / doing / done.

> 2026-11-21 customer change: **no topics or sub-topics**. Teachers work only with
> SLOs. See `docs/adr/0002-slo-only-no-topics.md`.

## Day 1 – book to clean data
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 0 | Install Node 22 + Python 3.12 | `node -v` shows v22, `python --version` shows 3.12 | M | done |
| 1 | Folder skeleton, .gitignore, PDF copied into `book/` (Izan copies) | `git status` does not show the PDF; skeleton pushed | M | done |
| 2 | Render all pages to images with PyMuPDF; record rotation per page and fix it | 196 images in `data/pages/`; every page checked upright | M | done |
| 3 | Map the book: chapter titles + page ranges, glossary range → `data/book.json` | 12 chapters + glossary listed; Izan confirms against the contents page | M | done |
| 4 | Izan types Chapter 1 SLOs → `data/ch01/slos.json` | File passes schema check; Izan says it matches the book | M (Izan) | done (9 SLOs) |
| 5 | Read Chapter 1 pages (Claude vision) → `data/ch01/text.json`, UNREADABLE marks | Passes schema; Izan spot-checks 2 pages against the book | M | done (Izan checked pages 5 and 13) |
| 6 | ADR 0001: offline question bank, no runtime AI | File exists, under 1 page | S | done |

Notes from task 2:
- Every PDF page is one book page scanned sideways: odd PDF pages turn 270°,
  even pages 90° (`data/page_rotations.json`). Re-create images with
  `.venv/Scripts/python.exe pipeline/render_pages.py --sheets`.
- Printed page number = PDF page − 3 (PDF page 4 = book page 1).

Notes from task 5:
- Transcripts per page in `data/ch01/pages/bNNN.txt` (marks explained in its README);
  `pipeline/build_text.py 1` builds `data/ch01/text.json` (202 blocks).
- The scan cuts words at the page edges: 104 of 202 blocks contain `[?...]` marks.
  Questions must quote only clean stretches of text (validator rule).

## Day 2 – SLO-only data, question bank
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 7 | Question schema + validator + tests | pytest passes, incl. outside word, fake SLO, fake excerpt | M | done |
| 8 | SLO-only migration: ADR 0002, remove topics (schema, build_text, validator, tests, topics.json), text `part` labels, SLO page map, capacity report | pytest passes; text.json has no topics; Izan confirmed SLO pages | M | done (25 tests; pages confirmed 2026-11-21) |
| 9 | Write Ch1 bank one SLO at a time (Short, MCQ, True/False) | All pass validator; capacity report per SLO × type | M | todo |
| 10a | Claude self-review: every question vs its quote (answer really in quote? tests its SLO? simple wording?); clear → `approved` "self-checked", doubtful → `pending` + reason | Every question approved or flagged | M | todo |
| 10b | Izan spot-check: all flagged + 2 random approved per SLO (~15 min) | Problems fixed or rejected | M (Izan) | todo |
| 10c | Simple review page: one question at a time with answer + quote, Approve / Reject | Izan can review with clicks only | S | todo |

## Day 3 – app, paper, rehearsal
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 11 | Next.js app: Class → Subject → Chapter → SLO checklist (with counts) → count 10/15/25 or Custom (1-30) → type (Short/MCQ/True-False/Mix) → Generate; layout works on phone and laptop | Every UI state below works; lint + typecheck pass | M | todo |
| 12 | Selection logic as a pure TS module (fair share across SLOs, Mix split, shortfall report) | Vitest: caps, round-robin spread, Mix redistribution, no fact reused, seeded randomness | M | todo |
| 13 | Print page (A4 print CSS) + optional answer key; browser Save as PDF | Print preview correct in Chrome | M | todo |
| 14 | Loading / empty / error states, every control works | Manual check list passes | M | todo |
| 14a | Installable offline web app (PWA): web manifest + hand-written service worker that caches the app and question data (no extra library) | Installs from the browser on laptop (Chrome) and Android phone; generates and prints a paper with internet switched off | M | todo |
| 15 | Chapters 2-3: SLOs (Izan types), transcripts, SLO pages, bank | Bank for those chapters reviewed | C | todo |
| 16 | Demo script + rehearsal | Full demo run twice without problems | M | todo |

## Design (SLO-only)

### Data and links
- `data/chNN/slos.json`: SLOs typed by Izan (`chNN-sloNN`) + `pages` merged from
  `data/chNN/slo_pages.json` (Claude proposes, Izan confirms).
- Question → `slo_id`. Its `page` must be in that SLO's `pages`, and its
  `source_excerpt` must appear word for word on that page in a `content` or
  `key_points` block (never `exercise` or `slo_list`).
- Types and marks: `mcq` 1, `true_false` 1, `short` 2.
- One book fact gives at most one question per type (validator: `(source_excerpt, type)` unique).

### How a paper is picked (app, no AI)
- `cap(slo, type)` = approved questions for that SLO and type.
- One type: shuffle each selected SLO's pool, take round-robin one per SLO,
  skip empty SLOs, stop at N. Result = min(N, Σ cap).
- Mix: targets ⌊N/3⌋ each, remainder to MCQ, then Short
  (10 → 4/3/3, 15 → 5/5/5, 25 → 9/8/8). Slots a type cannot fill move round-robin to
  the types with spare questions. Report per type: produced vs target, and why.
- No book fact appears twice in one paper (even across types).
- Only `approved` questions are used.

### UI states
| Situation | Teacher sees |
|---|---|
| No SLO selected | Generate disabled; "Select at least one SLO" |
| Custom count empty, < 1 or > 30 | Generate disabled; "Enter a number from 1 to 30" |
| Offline, app not installed yet | Browser's own offline page (first visit needs internet) |
| Requested > possible | Before: "Up to 12 questions possible". After: "12 of 15 generated – the selected SLOs have only 12 Short questions." |
| Type has 0 possible | Type option disabled, "0 available" |
| Mix not fully met | Paper with what exists + per-type report |
| SLO with no questions | Row disabled, "No questions yet" |
| Data failed to load | Error panel with retry |

### Paper layout (A4)
- **Header:**
  - school name (remembered on the device);
  - class, subject, chapter;
  - date (editable);
  - total marks, time allowed (optional);
  - Name / Roll No lines.
- **Sections** (only the ones used):
  - A MCQs "Encircle the correct option";
  - B True/False "Write T or F";
  - C Short Questions "Answer briefly".

  Each heading shows its marks, e.g. "(9 × 1 = 9)". Marks also appear beside each question.
- **Optional answer key** on a new page (answers + book page, for the teacher only).
  A **"Show SLO numbers"** checkbox adds the SLO number to each answer in the key.
  No SLO ids or quotes on the student paper.

### Decisions (Izan, 2026-11-21)
1. Fill-in-the-blank: dropped.
2. Mix split: even.
3. Answer key: has a "Show SLO numbers" checkbox (on/off).
4. The app must work **online and offline**: it is an installable web app (PWA) that
   teachers install from the website on laptop and mobile; after the first visit it works
   without internet.
5. Number of questions: buttons 10 / 15 / 25 plus a Custom box; Custom accepts 1-30.
   Values above 30 or below 1 show "Enter a number from 1 to 30" and block Generate.
6. PDF: browser print (Print → "Save as PDF" or a printer). No Playwright.
   On phones the same Print button opens the phone's print / save-as-PDF screen.

### Open questions
None right now.

### Risks
- Low-text SLOs (Ch1 SLO 1 "label parts" needs diagrams; SLO 9 has about one
  paragraph) will often give fewer questions than requested. This is intended.
- The SLO→page map is a judgment call. Mitigations: Izan confirms, and self-review checks each question's SLO fit.
- Cut-off words and book typos ("2 ATD", "reveres") reduce quotable facts.

## Folder layout
```
book/            scanned PDF (git-ignored)
docs/            PLAN.md, adr/
pipeline/        Python: render pages, schemas, build text, validator, reports, tests
data/pages/      page images (git-ignored)
data/book.json   chapters + page ranges
data/chXX/       slos.txt/slos.json (typed by Izan), slo_pages.json, pages/, text.json, questions.json
web/             Next.js app (to be built)
```

Question record: `id, chapter, slo_id, type (mcq|true_false|short), question,
options[], answer, marks, page, source_excerpt, review_status, review_note`.
