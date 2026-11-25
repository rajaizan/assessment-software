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
> on hold, see open question 6).

## Already done (still valid)
| # | Work | Reused how |
|---|---|---|
| 0-3 | Tools installed; book PDF rendered to upright page images; `data/book.json` (12 chapters, page ranges) | Unchanged. Pipeline works for any chapter. |
| 4 | Izan typed the Chapter 1 SLOs → `data/ch01/slos.json` (9 SLOs, statements only) | Kept. Needs SLO codes and cognitive levels added (task 1.1). |
| 5 | Chapter 1 transcribed → `data/ch01/pages/b001-b019.txt`, `text.json` (202 blocks, incl. the exercise on book pages 18-19) | The exercise questions are already transcribed. The chapter text is the source for answers and extra MCQs. |
| 7-8 | Question schema, validator (outside words, fake SLO, quote must match the page), 25 pytest tests; SLO→page map confirmed by Izan | Schema changes (task 1.2); the checks stay. |
| 9-10a | 174 Claude-written questions (57 MCQ, 63 T/F, 54 Short), self-reviewed | **Not the bank any more.** The best MCQs can become the "extra MCQs" (task 1.6). T/F and Short are kept in git history only. |
| 10b, 10c, 11-14a (old) | Spot-check, review page, old app plan | **Dropped / replaced** by the phases below. |

## Phase 1 – Chapter 1 data (bank JSON + coverage report)
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 1.1 | Izan adds each SLO's **code** and **cognitive level** exactly as printed in the book's SLO table → `slos.txt` / `slos.json` | Schema check passes; Izan says it matches the book | M (Izan) | todo |
| 1.2 | Schema v2 + validator + tests: `slo_ids[]`, type `mcq|short|long`, `cognitive_level`, `source` exercise/generated, `generated_note`, answer quote | pytest passes incl. new cases (note on exercise question → error; generated without note → error; unknown SLO or level → error) | M | todo |
| 1.3 | Exercise → `data/ch01/exercise.json`: exact printed text, options, page; unclear spots = UNREADABLE until Izan checks them | Validator passes; Izan has fixed the unclear spots from the book | M | todo |
| 1.4 | Map every exercise question to its SLO(s) → `data/ch01/coverage.md` (question → SLO table + uncovered SLOs) | Every exercise question mapped; Izan approves the mapping | M | todo |
| 1.5 | Answers for exercise questions, each from the chapter text with its page and quote (MCQ: correct option; Short/Long: model answer) | Validator passes; every answer has a page and a quote | M | todo |
| 1.6 | Extra questions by the rules: all SLOs covered → a few extra MCQs only (reuse the best of the 57); SLO uncovered → new questions for that SLO only. Each with its bracketed note | Validator passes; coverage report updated | M | todo |
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
| 3.2 | SLO list with Select all, code and cognitive-level tag | Works on phone and laptop | M | todo |
| 3.3 | Difficulty preset (Balanced / Easy / Challenging / Custom); Custom shows % per level with availability and a running total | Generate blocked until total = 100% | M | todo |
| 3.4 | MCQ / Short / Long count rows with live max; over max → "Can't generate more questions from the selected SLOs." | Messages come from the backend | M | todo |
| 3.5 | Review screen: Swap (disabled if none), Lock, Regenerate | Every button works | M | todo |
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
- `cognitive_level` comes from the SLO table, never invented (rule in open question 2).
- Marks (proposed): MCQ 1, Short 2, Long 5.

### How a paper is built (backend, no AI)
1. Pool = questions linked to at least one selected SLO.
2. Coverage first: for each selected SLO with no question yet, pick one random
   question of a requested type. If total count < number of SLOs → warning.
3. Fill the rest of each type's count at random, aiming at the difficulty target.
   If a level runs short, take from the nearest level (lower ↔ middle ↔ higher) and add a note.
4. No duplicate questions. Locked questions are kept on regenerate.
5. Swap: another unused question with the same type, SLO and level; disabled if none.

### Difficulty presets (proposed, % of questions per cognitive level)
| Preset | Lower | Middle | Higher |
|---|---|---|---|
| Easy | 60 | 30 | 10 |
| Balanced | 40 | 40 | 20 |
| Challenging | 20 | 40 | 40 |
Level names follow the book's SLO table once Izan has typed it.

### Paper layout (A4) – kept from the old plan
Header (school, class, subject, chapter, date, total marks, time, Name / Roll No);
sections A MCQs, B Short, C Long with marks per section. Answer key = separate
printout with answers, book page and (checkbox) SLO codes. Generated-question notes
appear in the answer key only (open question 5).

### Open questions (Izan / customer)
1. The brief says Chapter 1 SLOs are S-07-A-01 to S-07-A-08. Our Chapter 1 ("Plant System")
   has **9** SLOs with no codes. Does the book print codes and levels? Which chapter is meant?
2. Cognitive level is per SLO. When an exercise question maps to two SLOs with different
   levels, which level does it get? Proposal: the level of its main (first) SLO.
3. How many extra MCQs is "modest"? Proposal: 2 per SLO (about 18).
4. Exercise Short Q5 refers to a picture. Leave it out, keep it with "(diagram in book)",
   or print the picture?
5. Do generated-question notes appear on the student paper or only in the answer key?
6. The old plan made the app work offline on phones (ADR 0003). A backend means a server
   must run. For the demo: run on one laptop (`npm run dev`) and keep offline install for later?
7. Long-question marks: 5? Short questions with parts (a, b, c): still 2 marks?

### Risks
- Small bank (about 28 exercise questions + extras): Swap will often be disabled and
  difficulty fallback will happen often. This is expected; the notes explain it.
- Cut-off words in the scan (two exercise spots) need Izan to read the physical book.

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
