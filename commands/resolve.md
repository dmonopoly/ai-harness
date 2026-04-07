# `/resolve`

Use this command as the single entry point for the spec harness.

## Inputs

- The user message must include a ticket ID such as `ADT-123`.
- The rest of the message may include a ticket link, ticket contents, or a manual task description.

## Orchestration

1. Extract the ticket ID from the user message.
2. Check whether `~/.harness/<ticket-id>/` exists.
3. If the folder does not exist:
   - run `python3 ~/.harness/scripts/tasklog.py init <ticket-id>`
   - invoke the `planner` subagent
4. If the folder exists, inspect `~/.harness/<ticket-id>/tasks.json`.
5. Use this phase detection logic:
   - if there are no tasks, invoke `planner`
   - if any task is missing acceptance criteria, invoke `planner`
   - if any task has status `BLOCKED`, report the blocked tasks to the user and ask for guidance
   - if any task has status `IMPLEMENTED`, invoke `validator`
   - else if any task has status `NEEDS_WORK`, invoke `builder`
   - else if any task has status `AVAILABLE` and its dependencies are satisfied, invoke `builder`
   - else if all tasks are `VALIDATED`, report completion
   - else report that no ready task is available yet
6. Pass the ticket ID plus relevant ticket and harness context to the invoked subagent.

## Notes

- Keep this command thin; it is orchestration only.
- Do not duplicate the role instructions from the subagent files here.
- Treat harness files as durable resumable state.
