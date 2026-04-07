#!/usr/bin/env python3
"""Manage per-ticket task state for the spec harness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HOME = Path.home()
HARNESS_ROOT = HOME / ".harness"
TEMPLATES_ROOT = HARNESS_ROOT / "templates"

STATUS_VALUES = {
    "AVAILABLE",
    "WIP",
    "IMPLEMENTED",
    "VALIDATED",
    "NEEDS_WORK",
    "BLOCKED",
}

VALID_TRANSITIONS = {
    "AVAILABLE": {"WIP"},
    "WIP": {"IMPLEMENTED", "BLOCKED"},
    "IMPLEMENTED": {"VALIDATED", "NEEDS_WORK"},
    "NEEDS_WORK": {"WIP"},
    "BLOCKED": {"AVAILABLE"},
    "VALIDATED": set(),
}


class TasklogError(Exception):
    """Raised for user-facing tasklog failures."""


def ticket_dir(ticket_id: str) -> Path:
    return HARNESS_ROOT / ticket_id


def tasks_path(ticket_id: str) -> Path:
    return ticket_dir(ticket_id) / "tasks.json"


def spec_path(ticket_id: str) -> Path:
    return ticket_dir(ticket_id) / "spec.md"


def progress_log_path(ticket_id: str) -> Path:
    return ticket_dir(ticket_id) / "progress.log"


def load_template(name: str) -> str:
    path = TEMPLATES_ROOT / name
    if not path.exists():
        raise TasklogError(f"missing template: {path}")
    return path.read_text()


def ensure_ticket_initialized(ticket_id: str) -> dict[str, Any]:
    target_dir = ticket_dir(ticket_id)
    created = not target_dir.exists()
    target_dir.mkdir(parents=True, exist_ok=True)

    spec_file = spec_path(ticket_id)
    if not spec_file.exists():
        spec_template = load_template("spec-template.md")
        spec_file.write_text(
            spec_template.replace("{{TICKET_ID}}", ticket_id)
            .replace("{{SOURCE}}", "user message or ticket link")
            .replace("{{SUMMARY}}", "Fill in the summary before implementation.")
            .replace("{{GOAL_1}}", "Describe the primary outcome.")
            .replace("{{NON_GOAL_1}}", "Describe a deliberate non-goal.")
            .replace("{{CONSTRAINT_1}}", "List the most important constraint.")
            .replace("{{EDGE_CASE_1}}", "List the first meaningful edge case.")
            .replace("{{QUESTION_1}}", "List the first unresolved question.")
        )

    tasks_file = tasks_path(ticket_id)
    if not tasks_file.exists():
        tasks_template = load_template("tasks-template.json")
        tasks_file.write_text(tasks_template.replace("{{TICKET_ID}}", ticket_id))

    log_file = progress_log_path(ticket_id)
    if not log_file.exists():
        log_file.write_text("")

    return {"ticket_id": ticket_id, "created": created}


def load_tasks(ticket_id: str) -> dict[str, Any]:
    path = tasks_path(ticket_id)
    if not path.exists():
        raise TasklogError(f"missing tasks file: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TasklogError(f"invalid json in {path}: {exc}") from exc
    if data.get("ticket_id") != ticket_id:
        raise TasklogError(
            f"ticket mismatch: tasks.json has {data.get('ticket_id')!r}, expected {ticket_id!r}"
        )
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        raise TasklogError("tasks.json must contain a top-level 'tasks' list")
    return data


def save_tasks(ticket_id: str, data: dict[str, Any]) -> None:
    path = tasks_path(ticket_id)
    path.write_text(json.dumps(data, indent=2) + "\n")


def validate_task_shape(task: dict[str, Any]) -> None:
    required = {
        "id",
        "title",
        "requirement_ids",
        "acceptance_criteria_ids",
        "depends_on",
        "status",
        "files_or_symbols",
        "validation_notes",
        "needs_work_reason",
    }
    missing = sorted(required - set(task))
    if missing:
        raise TasklogError(f"task {task.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if task["status"] not in STATUS_VALUES:
        raise TasklogError(f"task {task['id']} has invalid status: {task['status']}")


def task_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for task in data["tasks"]:
        validate_task_shape(task)
        index[task["id"]] = task
    return index


def dependencies_validated(data: dict[str, Any], task: dict[str, Any]) -> bool:
    index = task_index(data)
    for dep_id in task["depends_on"]:
        dep = index.get(dep_id)
        if dep is None or dep["status"] != "VALIDATED":
            return False
    return True


def next_ready_task(data: dict[str, Any]) -> dict[str, Any] | None:
    for task in data["tasks"]:
        if task["status"] in {"AVAILABLE", "NEEDS_WORK"} and dependencies_validated(data, task):
            return task
    return None


def get_task(data: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in data["tasks"]:
        if task["id"] == task_id:
            validate_task_shape(task)
            return task
    raise TasklogError(f"unknown task: {task_id}")


def command_init(args: argparse.Namespace) -> None:
    result = ensure_ticket_initialized(args.ticket_id)
    state = "created" if result["created"] else "resumed"
    print(f"{state}\t{args.ticket_id}\t{ticket_dir(args.ticket_id)}")


def command_next(args: argparse.Namespace) -> None:
    data = load_tasks(args.ticket_id)
    task = next_ready_task(data)
    if task is None:
        print("NONE")
        return
    print(f"{task['id']}\t{task['status']}\t{task['title']}")


def command_claim(args: argparse.Namespace) -> None:
    data = load_tasks(args.ticket_id)
    task = get_task(data, args.task_id)
    if task["status"] not in {"AVAILABLE", "NEEDS_WORK"}:
        raise TasklogError(
            f"task {args.task_id} is {task['status']}; only AVAILABLE or NEEDS_WORK can be claimed"
        )
    if not dependencies_validated(data, task):
        raise TasklogError(f"task {args.task_id} is not ready; dependencies are not all VALIDATED")
    task["status"] = "WIP"
    save_tasks(args.ticket_id, data)
    print(f"claimed\t{task['id']}\tWIP")


def command_update(args: argparse.Namespace) -> None:
    if args.new_status not in STATUS_VALUES:
        raise TasklogError(f"invalid status: {args.new_status}")

    data = load_tasks(args.ticket_id)
    task = get_task(data, args.task_id)
    current_status = task["status"]
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if args.new_status not in allowed:
        raise TasklogError(f"invalid transition: {current_status} -> {args.new_status}")

    if args.new_status == "WIP" and current_status in {"AVAILABLE", "NEEDS_WORK"}:
        if not dependencies_validated(data, task):
            raise TasklogError(f"task {args.task_id} is not ready; dependencies are not all VALIDATED")

    if args.new_status in {"NEEDS_WORK", "BLOCKED"}:
        task["needs_work_reason"] = args.reason or ""
    else:
        task["needs_work_reason"] = ""

    task["status"] = args.new_status
    save_tasks(args.ticket_id, data)
    print(f"updated\t{task['id']}\t{current_status}->{args.new_status}")


def command_summary(args: argparse.Namespace) -> None:
    data = load_tasks(args.ticket_id)
    print("ID\tSTATUS\tREADY\tDEPENDS_ON\tTITLE")
    for task in data["tasks"]:
        validate_task_shape(task)
        ready = (
            "yes"
            if task["status"] in {"AVAILABLE", "NEEDS_WORK"} and dependencies_validated(data, task)
            else "no"
        )
        depends_on = ",".join(task["depends_on"]) if task["depends_on"] else "-"
        print(f"{task['id']}\t{task['status']}\t{ready}\t{depends_on}\t{task['title']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage harness task state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize or resume a ticket folder")
    init_parser.add_argument("ticket_id")
    init_parser.set_defaults(func=command_init)

    next_parser = subparsers.add_parser("next", help="Show the next ready task")
    next_parser.add_argument("ticket_id")
    next_parser.set_defaults(func=command_next)

    claim_parser = subparsers.add_parser("claim", help="Claim a ready task")
    claim_parser.add_argument("ticket_id")
    claim_parser.add_argument("task_id")
    claim_parser.set_defaults(func=command_claim)

    update_parser = subparsers.add_parser("update", help="Transition a task to a new status")
    update_parser.add_argument("ticket_id")
    update_parser.add_argument("task_id")
    update_parser.add_argument("new_status")
    update_parser.add_argument("--reason", default="", help="Reason for NEEDS_WORK or BLOCKED")
    update_parser.set_defaults(func=command_update)

    summary_parser = subparsers.add_parser("summary", help="Print a concise task summary")
    summary_parser.add_argument("ticket_id")
    summary_parser.set_defaults(func=command_summary)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except TasklogError as exc:
        print(f"error\t{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
