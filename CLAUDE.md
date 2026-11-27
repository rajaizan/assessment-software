# Assessment Software – rules for Claude

## About Izan
CS student in Mirpur, AJK. Building by vibe coding. Give ONE step at a time,
in plain language, and wait for Izan before moving on. Do everything you can
yourself; only ask Izan for what you cannot do (e.g. checking against the real book).

## Project
Web app for government-school teachers to make print-ready papers from the
official textbook (Class 7 General Science, AJ&K / National Curriculum 2022-23).
Current goal: a working prototype for ONE chapter (Chapter 1) to show stakeholders.
Other chapters are added one at a time, only after approval. Later (NOT now):
Classes 8-9, more subjects, Urdu RTL, Term Exam mode, offline install, AI chat.
Plan and status: docs/PLAN.md. Big decisions: docs/adr/ (latest: ADR 0004).

## Truth rules (most important)
1. The book is the only source. Never use outside knowledge, facts or terms.
2. Never invent SLOs, SLO codes, cognitive levels, terms, page numbers or quotes.
3. SLOs come ONLY from data/chXX/slos.json, typed by Izan: statements from the book's
   SLO list; codes and cognitive levels from the client's coded SLO list (the book prints
   none). One code can cover several book SLOs (Ch1: S-07-A-06 = book SLOs 6 + 7).
   Level groups for difficulty: data/levels.json.
4. If text is cut off, blurry or unclear, write UNREADABLE. Never guess.
5. Page numbers = printed book page numbers; also store the PDF page index.
6. If unsure, stop and ask Izan.

## Question-bank rules (per chapter)
1. The bank starts from the chapter's own exercise (MCQ, short, long), copied exactly.
2. Map every exercise question to the SLO(s) it covers (slo_ids[]). Write a coverage
   report: question → SLO table, plus uncovered SLOs.
3. If the exercise covers ALL SLOs: keep all exercise questions and add 1 extra MCQ
   per SLO code. Add NO new short or long questions.
4. If an SLO is uncovered: keep all exercise questions and write new questions only
   for the uncovered SLOs.
5. Self-written questions use only the chapter's content and words, in short, simple
   sentences, and carry a bracketed note, e.g. "(Newly generated - SLO S-07-A-05, not
   covered in exercise)". Exercise questions carry no note.
6. Every answer comes from the chapter text and stores its page and exact quote.
7. Every question stores: id, chapter, type (mcq | short | long), text, options (MCQ),
   answer, slo_ids[], cognitive_level, source ("exercise" | "generated"), generated_note.
   No topics or sub-topics (ADR 0002). No true/false.
8. Every question must pass pipeline/validate_questions.py before it goes in the bank.
9. The pipeline must work for any chapter without code changes (data only).
10. Questions are made OFFLINE. The app never calls an AI at runtime.

## App rules
- All selection and validation logic lives in the backend (web/lib/server and API
  routes). The frontend only shows what the backend returns; it never repeats the logic.
- Every selected SLO gets at least one question. Random selection, no duplicates.
- Difficulty presets are targets: fill from the nearest level and say so.
- Counts above what the bank holds: "Can't generate more questions from the selected SLOs."
- The printed student paper never shows SLO codes, cognitive levels or generated-question
  notes. Levels show on the review screen; levels, notes and codes go in the answer key.

## How to work
- One task from docs/PLAN.md at a time. Check its "done when" test before calling it done.
- After each task: update docs/PLAN.md status, then commit and push.
- Vertical slice: finish Chapter 1 fully before other chapters.
- If behind: cut polish before cutting quality.
- Write a short ADR in docs/adr/ for big decisions.

## Code standards
Python 3.12 (pipeline, PyMuPDF, Pydantic, pytest). Next.js + strict TypeScript +
Tailwind + shadcn/ui + Zod (app and backend in one project, Vitest). Runs locally with
one command (`npm run dev` in web/). PDF = print CSS + browser "Save as PDF" (no Playwright).
npm, not pnpm. No unnecessary dependencies. Small modules, validate data at boundaries,
lint, tests for validator, selection, swap and regenerate, conventional commits
(feat:, fix:, docs:, chore:).

## UI standards
Established component library (shadcn/ui), neutral palette, one accent colour,
real loading/empty/error states. No gradients, emoji icons, lorem ipsum or dead
buttons. Every visible control must work; "coming soon" items are visibly disabled.

## Git & backup rules
- Never work directly on `main` for new features. Create a new branch for each feature or fix.
- Every time you finish a prompt or get a feature working, immediately run
  `git add .`, `git commit -m "clear description"`, and `git push -u origin HEAD`
  so the branch is backed up to GitHub.
- The book PDF and page images are git-ignored. Never commit them. Exception: small
  cropped figures that a question needs (e.g. web/public/figures/ch01-short05.png).

## Using Anthropic API credits
Not now. Claude Code itself reads page images and writes questions, chapter by
chapter. Use the API only if Izan says so after hitting plan limits.
