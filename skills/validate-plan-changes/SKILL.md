---
name: validate-plan-changes
description: Validates implemented plan or task changes before they are marked done. Use when the user asks to validate an implementation, check whether a branch or task works, or run the final verification pass on code changes. Runs targeted automated checks, fixes small validation blockers in a loop, and invokes `repo-runtime-validation` only when runtime behavior needs local smoke testing.
---

# Validate Plan Changes

## Contract

This skill is the validation orchestrator for implemented work.

Use it to answer: "Is this change ready?"

Do:
- state the validation plan first and wait briefly
- run focused automated checks for affected code
- fix small, clearly scoped validation blockers and re-run
- decide whether runtime validation is required
- load `repo-runtime-validation` only when local runtime smoke testing is needed
- write a validation log and report the outcome

Do not:
- start a local service for every change
- own repo-specific startup, port, config, or auth details
- rediscover runtime recipes by wandering through docs
- do unrelated refactors, migrations, or large feature work
- commit or push unless the user explicitly asked for that separately

## Trigger Rules

Use when:
- the user asks to validate a task, plan, branch, MR, or implementation
- a builder has finished code changes and needs a final verification pass
- the main question is whether the change works, passes checks, or is ready

Do not use when:
- the user only wants a code review
- the user only wants a local server started
- the task is only docs or planning with no code to verify

## State The Plan First

Before running anything, tell the user the exact validation plan:
- which tests or build commands you expect to run
- whether runtime validation is likely needed
- which service or endpoints would be checked if runtime validation runs

Pause briefly so the user can interrupt.

## Validation Workflow

1. Identify the affected scope from the task, acceptance criteria, and changed files.
2. Run the narrowest useful automated checks first.
   - Rust default: `cargo test -p <crate>` for affected crates.
   - If crate scoping is unclear, use the smallest broader command that covers the changed code.
   - If there are no meaningful tests, run a compile or build check instead and say so.
3. If a check fails because of a likely regression in changed code, investigate, make a small fix, and re-run.
4. After 4 failed attempts on the same test or check, or if the fix stops being small, stop and ask the user.
5. Decide whether runtime validation is needed.
   Run `repo-runtime-validation` only when:
   - executable service behavior changed
   - API, worker, or background job behavior changed
   - acceptance criteria require local smoke testing
   Skip it for docs-only changes, isolated refactors, test-only changes, or library-only edits unless the task explicitly calls for runtime checks.
6. Summarize passes, failures, fixes, and anything intentionally skipped.

## Token Efficiency

- Prefer one scoped test command over a workspace-wide command.
- Batch related inspection commands.
- Do not poll builds with repeated sleeps; use a long enough foreground timeout.
- If runtime validation is needed, hand off repo-specific startup and endpoint work to `repo-runtime-validation`.

## Validation Log

Write all commands run, outcomes, and any fixes to `/tmp/post-process-validation-log-<uuid>.txt` where `<uuid>` comes from `uuidgen`.

If `repo-runtime-validation` runs, include the runtime log path it produced in the same validation log.

## `rgp` — Lint, Format, Commit, Push

After **every code change that fixes a test(s), and that you have high confidence the change is excellent (>90%)**, commit with an informative commit message. If not confident, prefix the commit message with `[Low Confidence]`. Then run `rgp`. Do not skip.

```bash
bash .cursor/scripts/rgp.sh
```

Runs `cargo clippy --fix` + `cargo +nightly fmt`, commits (or amends if no prior diffs), pushes with `--force-with-lease`.

## Guardrails

- Stop immediately on 401, 403, expired credentials, SSH rejection, or VPN/access failures; ask the user to restore access.
- Never run schema migrations or other DDL as part of validation unless the user explicitly asks.
- Stop and ask if validation starts requiring broad code changes unrelated to the original task.
