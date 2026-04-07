---
name: repo-runtime-validation
description: Runs repo-specific local runtime smoke tests for changed services, workers, and endpoints. Use when a task changes executable behavior and you need to start a local service, verify health or endpoint behavior, capture logs, and clean up processes.
---

# Repo Runtime Validation

## Contract

This skill owns repo-specific runtime validation.

Use it after `validate-plan-changes`, or whenever the main need is: "Start the service locally and prove the changed runtime behavior works."

Do:
- state the runtime plan first and wait briefly
- use known startup recipes and checked-in config
- start the service on an explicit port with log capture
- verify the changed endpoints or workflows
- clean up every process you started
- report runtime outcomes and log locations

Do not:
- decide whether runtime validation is required in the first place
- run broad automated test suites except small prerequisites
- spend a long time exploring docs to invent a startup flow
- do unrelated bug fixing or large implementation work

## State The Plan First

Before running anything, tell the user:
- which service or binary will be started
- the working directory, command, and port
- which config or auth assumptions will be used
- which endpoints or workflows will be exercised

Pause briefly so the user can interrupt.

## Runtime Workflow

1. Check if there is an existing service port running from the current branch already and that is up-to-date. If so, reuse it.
2. If not, try `cargo run` or `npm run dev` or equivalent using an unused port.
3. If these fail, **ask the user** for the startup command, working directory, and port. One question saves 10+ tool calls. If you are stuck trying to start the service after 3 minutes, **stop trying and notify the user**.
4. Prefer the repo's checked-in runtime config and normal local startup flow.
5. Start the service with an explicit port. Always capture stdout and stderr to a dedicated log file (e.g. `/tmp/post-process-server-log-<uuid>.txt`). A human should be able to open the validation log and immediately see which server log file to inspect for the full runtime output.
6. Wait only as long as needed for startup, then run the smallest useful smoke checks for the changed behavior.
7. Record commands, outcomes, and server log path in `/tmp/post-process-validation-log-<uuid>.txt`, or append to an existing validation log if one already exists.
8. Clean up every process you started and verify the port is released.

## Known Server Recipes

| Service | Working directory | Start command | Default port |
|---|---|---|---|
| fanhub-sports-worker | `services/fanhub-sports-worker/` | `AWS_PROFILE=gsg-gsm-ci ../../target/debug/fanhub-sports-worker` (build first with `cargo build -p fanhub-sports-worker` from repo root) | 3000 |

If you need to verify Moments API endpoints, load `moments-api-curl` rather than rebuilding the request manually.

## Config And Access Rules

- Prefer `config-default.toml`, `config-local.toml`, or the repo's normal checked-in config path.
- If local and default config split responsibility (for example local host credentials in `config-local.toml` and database names/feature flags in `config-default.toml`), reason from both before changing anything.
- Use temporary config files only if the built-in config genuinely cannot support the validation you need.
- Always set `AWS_PROFILE` when starting a service that needs AWS. Try `AWS_PROFILE=gsg-gsm-ci` first. If it fails with an expired-token or credentials error, tell the user to run `aws sso login` and ask for the correct profile name.
- **CI/shared services are allowed**: it is okay for the local service to connect to CI/shared dependencies such as Redis, Content Graph, or similar supporting services when that is part of the normal local setup or the user explicitly allows it.
- On any 401, 403, SSH rejection, expired token, or VPN timeout — **stop immediately**. Tell the user to check VPN/SSO. Resume only after they confirm.

## Token Efficiency

- **Batch shell commands** — combine related checks (health check, port check, PID lookup) into a single `&&`-chained command.
- **Don't poll compilation.** Set the foreground timeout high enough for the build to finish (e.g., 180000ms for a full Rust build). One call, not three sleeps.
- **Parse Postman collection in one call** — extract login, target request URL, method, headers, and body in a single python3 invocation, not multiple passes.

## Process Management

- Use an **explicit port** (e.g., `--port 8081`) — another agent may occupy the default.
- **Track every process you start** in a checklist (servers, Docker containers, docker-compose services, background jobs). A `docker-compose up` or `docker run` counts just as much as a `cargo run`.
- **Always preserve local server logs** — redirect or tee stdout/stderr to a dedicated file and note that path in the validation log.
- **Kill all spawned processes** when validation is complete. Use `pkill -f <binary_name>` to kill the process tree in one shot, then verify with `lsof`. Don't chase individual PIDs.
- If you started a Docker container or docker-compose service, stop it with `docker stop` / `docker-compose down` during cleanup.

## Database And Test Data Safety

- Never run migrations or other DDL against non-local databases as part of runtime validation.
- Do not create a new local database just to make validation easier; ask the user first.
- Do not delete test rows you created.
- Prefix human-visible labels with `[AI-generated]` when creating local test data.

## Avoid Rabbit Holes

- If startup is unclear and no recipe exists, ask the user instead of spending more than 3 minutes exploring.
- Never sleep longer than 60 seconds waiting for a periodic process; restart or trigger refresh instead.
- If runtime validation would require large unrelated code changes, stop and ask.
