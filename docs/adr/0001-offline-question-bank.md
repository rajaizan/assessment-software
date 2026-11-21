# ADR 0001: Offline question bank, no AI at runtime

Date: 2026-11-20 · Status: accepted

## Context
The demo must be instant, free to run, and impossible to fail live. Questions must
come only from the textbook, with no outside facts.

## Decision
Questions are written offline (by Claude Code, chapter by chapter), checked by
`pipeline/validate_questions.py`, reviewed, and stored in `data/chNN/questions.json`.
The web app never calls an AI. It only picks questions at random from the approved bank.

## Consequences
- Paper generation is instant and costs nothing per use.
- Quality is controlled once, before release, by the validator and review.
- Variety is limited to the size of the bank. The bank must be large, and the app
  must say honestly when it has fewer questions than requested.
