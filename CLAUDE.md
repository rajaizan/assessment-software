# Assessment Software – rules for Claude

## About Izan
CS student in Mirpur, AJK. Building by vibe coding. Give ONE step at a time,
in plain language, and wait for Izan before moving on. Do everything you can
yourself; only ask Izan for what you cannot do (e.g. checking against the real book).

## Project
Web app for government-school teachers to make print-ready tests from the
official textbook. Current goal: demo prototype for ONE book, Class 7 Science
(English). Later (NOT now): Classes 7-9, more subjects, Urdu RTL, DOCX, AI chat,
licensing. Plan and status: docs/PLAN.md.

## Truth rules (most important)
1. The book is the only source. Never use outside knowledge, facts or terms.
2. Never invent SLOs, topics, terms, page numbers or quotes.
3. SLOs come ONLY from data/chXX/slos.json, typed by Izan from the physical book.
4. If text is cut off, blurry or unclear, write UNREADABLE. Never guess.
5. Page numbers = printed book page numbers; also store the PDF page index.
6. If unsure, stop and ask Izan.

## Question rules
1. Each question maps to exactly one SLO of its chapter.
2. Everything comes from the chapter text. No outside terms, jargon or facts.
3. Short, simple sentences for students with limited English.
4. Each question stores chapter, topic, SLO id, page, exact source excerpt.
5. MCQ wrong options also use only chapter words.
6. Every question must pass pipeline/validate_questions.py before it goes in the bank.
7. Questions are made OFFLINE. The app never calls an AI at runtime; it only picks randomly.

## How to work
- One task from docs/PLAN.md at a time. Check its "done when" test before calling it done.
- After each task: update docs/PLAN.md status, then commit and push.
- Vertical slice: finish Chapter 1 fully before other chapters.
- If behind: cut MCQ/mixed before cutting quality.
- Write a short ADR in docs/adr/ for big decisions.

## Code standards
Python 3.12 (pipeline, PyMuPDF, Pydantic, pytest). Next.js + strict TypeScript +
Tailwind + shadcn/ui + Zod (app, Vitest, Playwright for PDF). npm, not pnpm.
Small modules, validate data at boundaries, lint, tests for validator and
sampling, conventional commits (feat:, fix:, docs:, chore:).

## UI standards
Established component library (shadcn/ui), neutral palette, one accent colour,
real loading/empty/error states. No gradients, emoji icons, lorem ipsum or dead
buttons. Every visible control must work.

## Git & backup rules
- Never work directly on `main` for new features. Create a new branch for each feature or fix.
- Every time you finish a prompt or get a feature working, immediately run
  `git add .`, `git commit -m "clear description"`, and `git push -u origin HEAD`
  so the branch is backed up to GitHub.
- The book PDF and page images are git-ignored. Never commit them.

## Using Anthropic API credits
Not now. Claude Code itself reads page images and writes questions, chapter by
chapter. Use the API only if Izan says so after hitting plan limits.
