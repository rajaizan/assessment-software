# ADR 0003: Installable offline web app, browser print for PDF

Date: 2026-11-21 · Status: accepted (Izan)

## Context
Teachers in government schools often have weak or no internet. They use laptops
and phones. They need a printable paper, and we want no heavy dependencies.

## Decision
- The app is a **Progressive Web App**: a web manifest plus a small hand-written
  service worker that caches the app and the question data. Teachers install it from
  the website on a laptop or phone. After the first visit it works fully offline.
  No PWA library is added.
- The paper is a print-styled page (A4 print CSS). The **Print** button opens the
  browser's print screen, where the teacher chooses "Save as PDF" or a printer.
  This works the same on laptop and phone, online and offline. Playwright is not used.
- The number of questions is chosen with buttons for 10 / 15 / 25 or a Custom box (1-30).

## Consequences
- No server is needed to make PDFs. Hosting can be any static web host.
- The first visit needs internet. After a question-bank update, the service worker
  refreshes the cache on the next online visit.
- Print output can differ slightly between browsers. The demo uses Chrome, and the
  print CSS is tested there and on Android Chrome.
