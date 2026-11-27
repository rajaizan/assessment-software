# ADR 0004: Exercise-based question bank, selection in the backend

Date: 2026-11-25 · Status: accepted (Izan and client, 2026-11-26)

## Context
A customer meeting changed the plan. The customer does not want a large bank of
generated questions. Papers should be built from the book's own exercise, mapped to
the chapter's SLOs, with a working one-chapter prototype for stakeholders first.

## Decision
- The bank for each chapter = all exercise questions (MCQ, short, long) mapped to
  SLO(s), plus extra questions written by Claude only as the rules allow: a few extra
  MCQs if every SLO is covered, or new questions only for uncovered SLOs. Each extra
  question carries a bracketed note.
- Types are mcq, short and long. True/false is dropped. A question can cover more
  than one SLO (`slo_ids[]`). Each question has a cognitive level taken from the SLO table.
- The 174 questions from task 9 are not the bank. The best MCQs may be reused as
  extra MCQs; the rest stay in git history.
- Selection, availability, swap, lock/regenerate and validation run on the server
  inside the Next.js app (route handlers). One project, one command to run. Python
  stays for the offline pipeline only.
- Paper and answer key are print pages (browser Save as PDF), as in ADR 0003.

## Consequences
- Much smaller bank: Swap is often disabled and difficulty fallback is common.
- The app needs a running server. For the demo it runs on one laptop; the offline
  install from ADR 0003 comes later.
- The book prints no SLO codes or levels. They come from the client's coded SLO list,
  typed by Izan. One code can cover several book SLOs.
