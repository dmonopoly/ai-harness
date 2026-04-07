# Progress Log Format

Append entries in this shape:

```text
## 2026-05-31 14:02 UTC | builder | T3
Implemented retry logic for webhook delivery.
Verified: unit tests pass, integration test covering timeout scenario added.
Remaining: validator should check error-path coverage for 5xx responses.
```

Rules:

- Use UTC timestamps with minute granularity: `YYYY-MM-DD HH:MM UTC`
- Use one of the roles: `planner`, `builder`, `validator`
- Reference the task or requirement ID touched
- Keep entries append-only
- Cover what changed, what was verified, and what still needs attention
