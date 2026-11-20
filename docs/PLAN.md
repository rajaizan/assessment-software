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
| 2 | Render all pages to images with PyMuPDF; record rotation per page and fix it | 196 images in `data/pages/`; every page checked upright | M | todo |
| 3 | Map the book: chapter titles + page ranges, glossary range → `data/book.json` | 12 chapters + glossary listed; Izan confirms against the contents page | M | todo |
| 4 | Izan types Chapter 1 SLOs → `data/ch01/slos.json` | File passes schema check; Izan says it matches the book | M (Izan) | todo |
| 5 | Read Chapter 1 pages (Claude vision) → `data/ch01/text.json`: topics, text per page, UNREADABLE marks | Passes schema; Izan spot-checks 2 pages against the book | M | todo |
| 6 | ADR 0001: offline question bank, no runtime AI | File exists, under 1 page | S | todo |

## Day 2 – question bank, validator, app skeleton
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 7 | Question schema + validator (unknown words vs chapter text + `common_words.txt`, SLO exists, excerpt really in text, page in chapter range) | pytest passes, incl. tests that reject an outside word, fake SLO, fake excerpt | M | todo |
| 8 | Write Ch1 short-answer questions | ≥ 3 per SLO, all pass validator | M | todo |
| 9 | Write Ch1 MCQs | ≥ 3 per SLO, all pass validator | S | todo |
| 10 | Izan reviews Ch1 questions (approve/reject in a simple review list) | Every question has `review_status`; rejected ones fixed or removed | M (Izan) | todo |
| 11 | Next.js app: class/subject/chapter/topic pickers load from JSON | Page opens instantly with Class 7 / Science / Ch1 topics; lint + typecheck pass | M | todo |
| 12 | Random sampling (by chapter, topics, count, type) | Vitest passes: right count, no duplicates, only chosen topics, clear error if not enough questions | M | todo |

## Day 3 – PDF, polish, rehearsal
| # | Task | Done when | Pri | Status |
|---|---|---|---|---|
| 13 | Print layout: school name, class, subject, date, marks beside each question, total marks | Generated PDF looks right on A4 print preview | M | todo |
| 14 | PDF download via Playwright (fallback: print CSS + browser "Save as PDF") | Click Generate → PDF downloads in < 5 s | M | todo |
| 15 | Optional answer key (separate page) | Toggle works; key matches the questions | S | todo |
| 16 | Mixed paper (MCQ + short) | Mixed option works and is tested | C | todo |
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

Question record: `id, chapter, topic, slo_id, type (mcq|short), question,
options[], answer, marks, page, source_excerpt, review_status`.
