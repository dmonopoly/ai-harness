---
name: task-decomposition
description: Guides a planner through breaking a finished spec into small, well-bounded implementation tasks with explicit dependencies and validation notes.
---

# Task Decomposition

Use this skill when a planner needs to turn a finished spec into implementation tasks in `tasks.json`.

## Goal

Produce tasks that are small, independent when possible, and easy for a builder and validator to execute without re-planning the work.

## Decomposition Rules

- Make each task completable in roughly one focused session.
- Keep each task scoped to one concern and one area of the codebase.
- Prefer tasks that can be validated independently.
- When in doubt, split tasks smaller instead of broader.
- Avoid vague tasks such as "refactor" or "clean up" unless they have concrete acceptance criteria.

## Every Task Must Include

- a stable task ID like `T1`
- a one-line title
- `requirement_ids`
- `acceptance_criteria_ids`
- `depends_on`
- a valid workflow status
- likely `files_or_symbols`
- `validation_notes` describing the proof expected from the validator
- `needs_work_reason`, initialized to an empty string

## Quality Checks

- Acceptance criteria must be explicit, not implied.
- Dependencies must reflect the real execution order.
- `validation_notes` should name the expected validation level such as unit, integration, API, UI, smoke, or manual.
- Do not create giant umbrella tasks when two or more smaller tasks would be easier to build and validate.
