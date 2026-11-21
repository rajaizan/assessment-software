# ADR 0002: Teachers work with SLOs only, no topics

Date: 2026-11-21 · Status: accepted (customer meeting)

## Context
The first design let teachers pick chapter topics (1.1, 1.2, …) or SLOs. The customer
does not want topics or sub-topics. Teachers think in SLOs (Student Learning
Outcomes), which the curriculum defines per chapter.

## Decision
- Topics are removed from the UI, the data model, the validator and the generation logic.
- Every question belongs to exactly one SLO (`slo_id`).
- Each SLO lists the book pages that teach it (`data/chNN/slo_pages.json`, merged into
  `slos.json`). A question's source page must be one of its SLO's pages.
- Book text blocks keep only a `part` label (`content`, `slo_list`, `key_points`,
  `exercise`). Only `content` and `key_points` may be quoted as a source.
- Question types: `mcq` (1 mark), `true_false` (1 mark), `short` (2 marks).
  Fill-in-the-blank is dropped.
- The requested number of questions is a target. The app returns at most what the
  approved bank holds for the chosen SLOs and type, and explains any shortfall.
  One book fact gives at most one question per type (validator rule), so the bank
  cannot be padded with reworded copies.
- Mix papers split the count evenly over the three types (remainder to MCQ, then
  Short). Slots a type cannot fill move to the other types.
- The printable paper uses print CSS and the browser's Save as PDF. Playwright is dropped.

## Consequences
- Removed: `data/ch01/topics.json`, `Topic` and `Question.topic` in `pipeline/schemas.py`,
  topic checks in the validator and tests.
- The SLO→page map is a judgment call. Claude proposes it and Izan confirms it.
- SLOs with little text behind them (for example Ch1 SLO 9) will support only a few
  questions. Teachers will see "fewer than requested" for them. This is intended.
