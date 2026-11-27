# Plan – Class 7 General Science assessment-paper generator

Goal: a working **Chapter 1 prototype** to show stakeholders. A teacher picks the book,
the chapter, the SLOs, an optional difficulty preset and how many MCQ / Short / Long
questions they want. The app builds a paper from a question bank that is based on
**the book's own exercise**, lets the teacher swap and lock questions, and prints the
paper and a separate answer key. More chapters come only after stakeholders approve.

Legend: **M** = must, **S** = should, **C** = cut unless ahead.
Owner is Claude unless marked "Izan". Status: todo / doing / done / dropped.

> 2026-11-25 customer change (ADR 0004): the bank is the chapter exercise mapped to
> SLOs, plus a few extra questions written by Claude only where needed. No large
> generated bank, no True/False. Selection logic lives in the backend.
> Earlier changes: ADR 0002 (SLOs only, no topics), ADR 0003 (print and PWA; the PWA part is
> on hold: the demo runs on one laptop).

## Already done (still valid)
| # | Work | Reused how |
|---|---|---|
| 0-3 | Tools installed; book PDF rendered to upright page images; `data/book.json` (12 chapters, page ranges) | Unchanged. Pipeline works for any chapter. |
| 4 | Izan typed the Chapter 1 SLOs → `data/ch01/slos.json` (9 SLOs, statements only) | Kept. Codes and cognitive levels from the client's list are added in task 1.1. |
| 5 | Chapter 1 transcribed → `data/ch01/pages/b001-b019.txt`, `text.json` (202 blocks, incl. the exercise on book pages 18-19) | The exercise questions are already transcribed. The chapter text is the source for answers and extra MCQs. |
| 7-8 | Question schema, validator (outside words, fake SLO, quote must match the page), 25 pytest tests; SLO→page map confirmed by Izan | Schema changes (task 1.2); the checks stay. |
| 9-10a | 174 Claude-written questions (57 MCQ, 63 T/F, 54 Short), self-reviewed | **Not the bank any more.** The best MCQs can become the "extra MCQs" (task 1.6). T/F and Short are kept in git history only. |
| 10b, 10c, 11-14a (old) | Spot-check, review page, old app plan | **Dropped / replaced** by the phases below. |

## Phase 1 – Chapter 1 data (bank JSON + coverage report)
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 1.1 | Add each SLO's **code** and **cognitive level** from the client's coded SLO list → `slos.txt` / `slos.json`; level groups → `data/levels.json` | Schema check passes; Izan confirms codes and levels | M (Izan + Claude) | done (2026-11-27: 9 book SLOs → 8 codes; 35 tests pass) |
| 1.2 | Schema v2 + validator + tests: `slo_ids[]`, type `mcq|short|long`, `cognitive_level`, `source` exercise/generated, `generated_note`, answer quote | pytest passes incl. new cases (note on exercise question → error; generated without note → error; unknown SLO or level → error) | M | todo |
| 1.3 | Exercise → `data/ch01/exercise.json`: exact printed text, options, page; crop the Short Q5 picture → `web/public/figures/ch01-short05.png` (committed) | Validator passes; picture crop looks right | M | todo (the 2 unclear spots were fixed from the book on 2026-11-26) |
| 1.4 | Map every exercise question to its SLO(s) → `data/ch01/coverage.md` (question → SLO table + uncovered SLOs) | Every exercise question mapped; Izan approves the mapping | M | todo |
| 1.5 | Answers for exercise questions, each from the chapter text with its page and quote (MCQ: correct option; Short/Long: model answer) | Validator passes; every answer has a page and a quote | M | todo |
| 1.6 | Extra questions by the rules: all SLOs covered → **1 extra MCQ per SLO code** (8; reuse the best of the 57); SLO uncovered → new questions for that SLO only. Each with its bracketed note | Validator passes; coverage report updated | M | todo |
| 1.7 | `pipeline/build_bank.py N` → `data/chNN/bank.json` + coverage report; works for any chapter with no code changes | Running it for chapter 1 gives the bank; a dry run on chapter 2's folder fails only for missing data, not missing code | M | todo |
| 1.8 | Izan spot-checks the bank (all generated questions + 5 exercise answers) | Problems fixed | M (Izan) | todo |

## Phase 2 – Backend (server-side TypeScript in the Next.js app)
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 2.1 | Next.js skeleton in `web/`; bank loader validates `bank.json` with Zod at start | Bad bank file → clear error; lint + typecheck pass | M | todo |
| 2.2 | `GET /api/books`, `/api/chapters` (only Ch1 active, term-exam flag), `/api/chapters/1/slos` | Vitest route tests pass | M | todo |
| 2.3 | `POST /api/availability`: for chosen SLOs → available count per type and per type × level | Vitest: counts match bank; questions shared by two SLOs counted once | M | todo |
| 2.4 | `POST /api/generate`: every selected SLO first, then difficulty target with nearest-level fallback + notes, random, no duplicates, seeded | Vitest: coverage, fallback, caps, no duplicates, same seed = same paper | M | todo |
| 2.5 | `POST /api/swap` and regenerate with locked questions (stateless: browser sends the current paper and locks) | Vitest: swap keeps type + SLO + level, none left → disabled; locked stay on regenerate | M | todo |
| 2.6 | Validation errors from the server: count above max, count below number of SLOs (warning), Custom % not 100 | Vitest: each message returned | M | todo |
| 2.7 | Print views: paper and answer key as separate A4 pages (print CSS → browser "Save as PDF") | Chrome print preview correct for both | M | todo |

## Phase 3 – UI (shadcn/ui), wired to the backend
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 3.1 | Book → chapter(s); only Ch1 active; selecting all chapters of a term shows "Term Exam – coming soon" (disabled) | Clicks work; disabled items explain why | M | todo |
| 3.2 | SLO list (8 codes) with Select all, code and cognitive-level tag | Works on phone and laptop | M | todo |
| 3.3 | Difficulty preset (Balanced / Easy / Challenging / Custom); Custom shows % per level with availability and a running total | Generate blocked until total = 100% | M | todo |
| 3.4 | MCQ / Short / Long count rows with live max; over max → "Can't generate more questions from the selected SLOs." | Messages come from the backend | M | todo |
| 3.5 | Review screen: Swap (disabled if none), Lock, Regenerate; each question shows its cognitive level | Every button works | M | todo |
| 3.6 | Print paper / Print answer key buttons; loading, empty and error states | Manual check list passes | M | todo |

## Phase 4 – Demo polish and QA
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 4.1 | QA check list over the whole flow, on laptop and phone | All items pass | M | todo |
| 4.2 | Demo script + two rehearsals | Two clean runs | M | todo |

## Phase 5 – After stakeholder approval
Add chapters one at a time: Izan types SLOs (with codes and levels) → transcribe →
exercise → mapping → bank, using the Phase 1 pipeline unchanged. Later still: Classes
8-9, more subjects, Urdu RTL, Term Exam mode, offline install (if approved).

## Design

### Question record (`bank.json`)
`id, chapter, type (mcq|short|long), text, options[] (MCQ), answer, marks,
slo_ids[], cognitive_level, source (exercise|generated), generated_note,
question_page, answer_page, answer_excerpt`.
- `generated_note` example: "(Newly generated - SLO <code>, not covered in exercise)".
  For extra MCQs when every SLO is covered: "(Newly generated - SLO <code>, extra MCQ)".
  Exercise questions: empty.
- `slo_ids` hold the client's **codes** (S-07-A-01 …). Book SLOs 6 and 7 share S-07-A-06,
  so Chapter 1 has 9 book SLOs but 8 codes; the app lists the 8 codes.
- `cognitive_level` = level of the question's first code in `slos.json`, never invented.
- Marks: MCQ 1, Short 2, Long 5 (approved).

### How a paper is built (backend, no AI)
1. Pool = questions linked to at least one selected SLO.
2. Coverage first: for each selected SLO with no question yet, pick one random
   question of a requested type. If total count < number of SLOs → warning.
3. Fill the rest of each type's count at random, aiming at the difficulty target.
   If a level runs short, take from the nearest level (lower ↔ middle ↔ higher) and add a note.
4. No duplicate questions. Locked questions are kept on regenerate.
5. Swap: another unused question with the same type, SLO and level; disabled if none.

### Difficulty presets (approved, % of questions per level group)
| Preset | Lower | Middle | Higher |
|---|---|---|---|
| Easy | 60 | 30 | 10 |
| Balanced | 40 | 40 | 20 |
| Challenging | 20 | 40 | 40 |

Level groups (client-approved): **Lower** = Knowledge; **Middle** = Understanding;
**Higher** = Application, Analysis, Evaluate (anything above Understanding).
Stored in `data/levels.json`.

### Paper layout (A4) – kept from the old plan
Header (school, class, subject, chapter, date, total marks, time, Name / Roll No);
sections A MCQs, B Short, C Long with marks per section. Short Q5 prints its picture.
The student paper shows **no** SLO codes, cognitive levels or generated-question notes.
Answer key = separate printout with answers, book page, cognitive level,
generated-question notes, and (checkbox) SLO codes.

### Decisions (Izan / client, 2026-11-26)
1. Chapter 1 = "Plant System". The book prints no SLO codes or levels; they come from the
   client's coded list. Codes: S-07-A-01…05 = book SLOs 1…5, **S-07-A-06 = book SLOs 6 + 7**,
   S-07-A-07 = book SLO 8, S-07-A-08 = book SLO 9 (order approved by the client).
2. Level groups: Lower = Knowledge, Middle = Understanding, Higher = Application,
   Analysis, Evaluate.
3. Extra MCQs: 1 per SLO code (8).
4. Generated-question notes: answer key only.
5. Cognitive levels: shown on the review (swap/lock) screen and in the answer key,
   never on the printed paper.
6. Short Q5 picture is printed; a small crop of it is committed (page images stay ignored).
7. Demo runs on one laptop (`npm run dev`); offline install comes later.
8. Marks MCQ 1 / Short 2 / Long 5 and the difficulty presets are approved.
9. Exercise unclear spots read from the book: MCQ 4 d = "mesophyll tissues";
   MCQ 10 = "…if there would be no photosynthesis?".

10. Levels per code (client, 2026-11-27): 01 Evaluate, 02 Understanding, 03 Knowledge,
    04 Knowledge, 05 Understanding, 06 Understanding, 07 Evaluate, 08 Evaluate.
11. A question that maps to several codes takes the level of its **first** code.
12. A short question with parts (a, b, c) is still 2 marks in total.

### Open questions (Izan / client)
None right now.

### Risks
- Small bank (about 28 exercise questions + extras): Swap will often be disabled and
  difficulty fallback will happen often. This is expected; the notes explain it.
- Cut-off words in the scan may hide answers; answers must quote only clean text.

## Folder layout
```
book/            scanned PDF (git-ignored)
docs/            PLAN.md, adr/
pipeline/        Python: render pages, schemas, build text, validator, build_bank, tests
data/pages/      page images (git-ignored)
data/book.json   chapters + page ranges
data/chXX/       slos.txt/json, slo_pages.json, pages/, text.json, exercise.json, bank.json, coverage.md
web/             Next.js app: UI + backend route handlers (web/lib/server/ holds all selection logic)
```
