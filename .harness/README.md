# Spec Harness

The spec harness is a global workflow for driving complex work from a durable ticket ID such as `ADT-123`.

It keeps reusable agent behavior under `~/.cursor/` and keeps per-ticket execution state under `~/.harness/`, so active work can be resumed, inspected, and archived without mixing runtime artifacts into Cursor configuration.

## Quickstart

1. Start with a ticket ID and either a ticket link, ticket contents, or a manual task description.
2. Run `/resolve ADT-123`.
3. If the ticket is new, the harness initializes `~/.harness/ADT-123/` and sends the work to the planner.
4. Re-run `/resolve ADT-123` to continue through build and validation phases until all tasks are `VALIDATED`.

## Layout

- `~/.harness/templates/`: durable templates for `spec.md`, `tasks.json`, and progress log format
- `~/.harness/scripts/tasklog.py`: canonical task-state mutator
- `~/.harness/scripts/smoke_test.py`: end-to-end mechanical test
- `~/.harness/<ticket-id>/spec.md`: durable spec for the ticket
- `~/.harness/<ticket-id>/tasks.json`: task list and statuses
- `~/.harness/<ticket-id>/progress.log`: append-only execution trail

## Why Ticket IDs Matter

- The ticket ID is the stable handle for all work on that story.
- It gives the planner, builder, and validator one shared durable state folder.
- It makes resume behavior explicit: if the ticket folder already exists, the run resumes instead of starting from scratch.

## Phase Auto-Detection

`/resolve` should inspect `~/.harness/<ticket-id>/tasks.json` and pick the next role:

- no ticket folder yet: initialize and invoke `planner`
- no tasks, or tasks missing acceptance criteria: invoke `planner`
- any task is `BLOCKED`: report the blocked tasks and ask the user for guidance
- any task is `IMPLEMENTED`: invoke `validator`
- any task is `NEEDS_WORK`: invoke `builder`
- any ready task is `AVAILABLE`: invoke `builder`
- all tasks are `VALIDATED`: report completion

## How The Roles Interact

- `planner` sharpens the ticket into `spec.md`, decomposes it into bounded tasks, and records planning context in `progress.log`
- `builder` claims exactly one ready task, implements only that task, records verification, and marks it `IMPLEMENTED` or `BLOCKED`
- `validator` independently checks a built task, records findings, and marks it `VALIDATED` or `NEEDS_WORK`

## Support Skills

- `spec-interviewing`: helps the planner ask only the high-value clarification questions
- `task-decomposition`: helps the planner create bounded tasks with explicit validation notes
- `validate-plan-changes`, `cleanup-tests`, and `repo-runtime-validation`: optional validator helpers when the task calls for them

## Repo Discovery

By default, builders and validators read the repository `README.md` to discover canonical build, run, lint, and test commands.

If the README is ambiguous, stale, or spread across multiple files, add a small repo-local `.cursor/repo-profile.md` as a focused override.

## `tasklog.py`

Use `tasklog.py` instead of hand-editing task status:

```sh
python3 ~/.harness/scripts/tasklog.py init ADT-123
python3 ~/.harness/scripts/tasklog.py next ADT-123
python3 ~/.harness/scripts/tasklog.py claim ADT-123 T1
python3 ~/.harness/scripts/tasklog.py update ADT-123 T1 IMPLEMENTED
python3 ~/.harness/scripts/tasklog.py summary ADT-123
```

`tasklog.py` enforces dependency-aware readiness and valid status transitions.

## Resuming Existing Work

If `~/.harness/<ticket-id>/` already exists, treat it as the source of durable story state:

1. start from the latest user message or ticket contents
2. read `spec.md`
3. read `tasks.json`
4. read recent `progress.log` entries
5. continue with `/resolve <ticket-id>`

## Stale `WIP` Tasks

If a task is stuck in `WIP`, do not code around the ambiguity. Use `tasklog.py` to move it into an explicit recovery state, typically:

```sh
python3 ~/.harness/scripts/tasklog.py update ADT-123 T2 BLOCKED --reason "Builder stopped mid-task; needs re-triage"
python3 ~/.harness/scripts/tasklog.py update ADT-123 T2 AVAILABLE
```

If the real problem is missing requirements, update `spec.md` first and then re-run `/resolve`.

## When To Update The Spec

Update `spec.md` instead of improvising in code when:

- the ticket omits a meaningful edge case
- two requirements conflict
- rollout, observability, or rollback behavior is unclear
- the builder would otherwise make a product or architecture decision without approval

## End-To-End Example

1. `/resolve ADT-123` creates `~/.harness/ADT-123/` and invokes `planner`
2. the planner writes `spec.md`, creates tasks in `tasks.json`, and appends a planning entry to `progress.log`
3. `/resolve ADT-123` invokes `builder`, which claims the next ready task and implements it
4. the builder marks the task `IMPLEMENTED` and appends what changed and what was verified
5. `/resolve ADT-123` invokes `validator`, which independently checks the task
6. the validator marks the task `VALIDATED` or `NEEDS_WORK` and appends findings
7. repeat until the summary shows every task as `VALIDATED`

## Troubleshooting

- `error missing template`: recreate the missing file under `~/.harness/templates/`
- `invalid transition`: check the task's current status with `summary` and follow the supported workflow
- `NONE` from `next`: either there is no ready work, dependencies are not validated yet, or the plan needs to be updated
- planner keeps getting invoked: at least one task is still missing acceptance criteria
- builder or validator cannot find repo commands: update the repository `README.md` or add `.cursor/repo-profile.md`
