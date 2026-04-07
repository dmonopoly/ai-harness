# Ticket: ADT-000

## Source

- User request: Python demo under new `ai-harness-demo/` in repo `sysd-simulator` (`/Users/david.zhang/Workspace-Personal/sysd-simulator`).
- Deliverables: `web_scraper.py`, `sentiment_tagger.py`, `viewer.py`, `main.py`.

## Summary

Add a self-contained Python demo package that pulls a handful of current news headlines/descriptions from the public web, normalizes each into a short text snippet (up to 140 characters), labels each snippet with emotion-oriented sentiment using a maintained third-party library, and prints a readable table via a CLI entrypoint.

## Goals

- **G1:** Fetch **3–5** distinct news items from the live web without hard-coding final article text (URLs or feeds may be fixed).
- **G2:** Produce one **snippet string per item**, length **0–140 characters** (inclusive), suitable for tagging (trim whitespace; truncate with a clear ellipsis or word boundary where reasonable).
- **G3:** Attach **emotion/sentiment labels** to each snippet using a **currently maintained** Python library (see R3).
- **G4:** Expose **`viewer.py`** that prints a **table** (aligned columns or rich/tabulate-style) with at least: index, snippet, and tag(s).
- **G5:** **`main.py`** runs the full pipeline end-to-end when executed.

## Non-Goals

- No persistence (database, files) beyond optional cache for this demo.
- No web UI or API server.
- No changes to existing non-demo code in the repo outside `ai-harness-demo/`.

## User-Facing Behavior Or Workflow

1. Operator creates a venv, installs dependencies from `ai-harness-demo/requirements.txt`.
2. Operator runs `python main.py` from `ai-harness-demo/` (or `python -m` if structured that way—implementation choice documented in README).
3. Script fetches news, builds snippets, tags them, prints the table to stdout.
4. Exit code 0 on success; non-zero on unrecoverable failure with a short error message on stderr.

## Constraints

- All new code lives under **`ai-harness-demo/`** at the repository root.
- **Python 3.10+** (match common ecosystem defaults; state exact minimum in README if stricter).
- **Network access** at runtime is allowed for scraping/tagging if the chosen stack requires it.
- Dependencies must be **installable via pip** and declared in **`requirements.txt`** with reasonable version pins or ranges.

## Edge Cases And Failure Modes

- **Network/RSS/HTML failures:** Retry or skip with a clear stderr message; still aim to output **at least 3** items when the source is partially available, or exit with failure if fewer than 3 can be obtained.
- **Empty or very short source text:** Still emit a snippet (may be shorter than 140 chars; empty only if source is truly empty).
- **Model/library download (e.g. Hugging Face):** First run may download weights; document this and keep a **small** model or a lightweight alternative so the demo remains practical on a laptop.

## Observability And Rollback Notes

- **Observability:** Progress and errors on stderr; final table on stdout.
- **Rollback:** Delete the `ai-harness-demo/` directory; no other repo files are touched.

## Open Questions

- **OQ1:** Preferred primary news source (RSS feeds vs. single news page HTML) is left to the implementer; must be documented in README.
- **OQ2:** Emotion taxonomy: spec expects **at least one categorical label per snippet** (e.g. joy, anger, neutral). Exact label set follows the chosen model/library; document the mapping if the library returns scores or multi-label output.

## Requirements

- **R1:** Project scaffold: `ai-harness-demo/` with `requirements.txt` and a short `README.md` (setup, run, limitations).
- **R2:** `web_scraper.py` implements fetching and snippet extraction per G1–G2; exposes a function or small API the rest of the demo can import (e.g. `list[dict]` with `snippet` and optional `title`, `url`).
- **R3:** `sentiment_tagger.py` uses a **maintained** library (e.g. `transformers` + a small emotion or sentiment model, or another actively maintained package) to produce **human-readable labels** per snippet; pure random/mock tagging is not acceptable.
- **R4:** `viewer.py` formats and prints the table per G4, consuming structured input from the scraper/tagger pipeline.
- **R5:** `main.py` wires scraper → tagger → viewer in one run per G5.

## Acceptance Criteria

- **AC1:** `ai-harness-demo/requirements.txt` exists and `pip install -r requirements.txt` succeeds on a clean venv (documented Python version).
- **AC2:** README documents how to run the demo from the `ai-harness-demo` directory.
- **AC3:** Running the scraper module/API yields **3–5** items with **non-empty** snippets; each snippet has **len ≤ 140** (Unicode code points or documented definition).
- **AC4:** Each item receives **≥1** sentiment/emotion-related label from the chosen library; implementation does not use placeholder random labels.
- **AC5:** `viewer.py` prints a **tabular** layout with snippet and label columns (plus index or URL if available).
- **AC6:** `python main.py` (as documented) runs the full pipeline once and exits 0 on success.
- **AC7:** Failure modes (network, parse errors) produce actionable stderr output and non-zero exit when the pipeline cannot meet the 3-item minimum.
- **AC8:** No files outside `ai-harness-demo/` are added or modified for this ticket.
