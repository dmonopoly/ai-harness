---
name: spec-interviewing
description: Guides a planner through asking only the highest-value clarification questions needed to turn a rough request or ticket into a spec with explicit requirements, edge cases, and acceptance criteria.
---

# Spec Interviewing

Use this skill when a planner needs to turn a ticket or rough request into a spec that is clear enough to decompose into execution tasks.

## Goal

Ask only the high-leverage questions needed to remove ambiguity that would otherwise cause wasted implementation or validation work.

## Working Rules

- Start from what is already known in the user message, ticket, repository docs, and existing harness files.
- Skip questions whose answers are already explicit.
- Prefer questions about tradeoffs, limits, and failure handling over obvious basics.
- Stop once the spec is clear enough to write requirements, acceptance criteria, and bounded tasks.
- If the user does not answer a non-critical question, record an assumption in `spec.md` instead of stalling forever.

## Areas To Probe

- Failure modes and error handling
- Concurrency and race conditions
- Performance and scale expectations
- Security, permissions, and authentication
- Rollback and reversibility
- Observability, logging, and debugging needs
- UX ambiguity and edge cases
- Deployment and rollout concerns
- Dependencies on external systems
- Data migration or backward compatibility concerns

## Output Standard

Before finishing the interview, make sure the spec captures:

- concrete goals and non-goals
- user-facing behavior or workflow
- constraints and edge cases
- observability and rollback notes
- explicit requirement IDs such as `R1`
- explicit acceptance criteria IDs such as `AC1`
- any remaining open questions or assumptions
