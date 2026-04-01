#!/usr/bin/env python3
"""Validate cross-file runtime isolation invariants for clawhost-kit."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config_boundary import ValidationError, load_config, validate_config


class IsolationError(Exception):
    """Raised when runtime isolation invariants are violated."""


def _as_path(value: str) -> Path:
    return Path(value).expanduser()


def _assert_under(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise IsolationError(f"{label} must be inside {root}, got {path}") from exc


def _validate_positive_int(value: Any, label: str) -> None:
    if not isinstance(value, int) or value < 1:
        raise IsolationError(f"{label} must be a positive integer")


def validate_runtime_isolation(host: dict[str, Any], project: dict[str, Any], task: dict[str, Any]) -> None:
    if host.get("scope") != "host-global":
        raise IsolationError("first config must be host-global")
    if project.get("scope") != "project-instance":
        raise IsolationError("second config must be project-instance")
    if task.get("scope") != "per-task-ephemeral":
        raise IsolationError("third config must be per-task-ephemeral")

    for name, data in [("host", host), ("project", project), ("task", task)]:
        validate_config(data, source=name)

    concurrency = host["concurrency"]
    _validate_positive_int(concurrency.get("max_active_instances"), "concurrency.max_active_instances")
    _validate_positive_int(concurrency.get("max_parallel_tasks"), "concurrency.max_parallel_tasks")

    instance_root = _as_path(project["paths"]["instance_root"])
    state_root = _as_path(project["paths"]["state_root"])
    worktrees_root = _as_path(project["paths"]["worktrees_root"])
    cursor_file = _as_path(project["poller"]["cursor_file"])

    _assert_under(state_root, instance_root, "project state_root")
    _assert_under(worktrees_root, instance_root, "project worktrees_root")
    _assert_under(cursor_file, state_root, "project poller.cursor_file")

    if task["instance_id"] != project["instance_id"]:
        raise IsolationError(
            f"task instance_id {task['instance_id']} does not match project instance_id {project['instance_id']}"
        )

    worktree_path = _as_path(task["worktree"]["path"])
    _assert_under(worktree_path, worktrees_root, "task worktree.path")

    artifact_paths = task["artifacts"]
    for key, raw_path in artifact_paths.items():
        _assert_under(_as_path(raw_path), state_root, f"task artifacts.{key}")


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(
            "usage: python3 tools/runtime_isolation.py <host-global.json> <project-instance.json> <task-ephemeral.json>",
            file=sys.stderr,
        )
        return 2

    try:
        host = load_config(Path(argv[1]))
        project = load_config(Path(argv[2]))
        task = load_config(Path(argv[3]))
        validate_runtime_isolation(host, project, task)
    except (OSError, ValidationError, IsolationError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print(f"PASS {argv[1]}")
    print(f"PASS {argv[2]}")
    print(f"PASS {argv[3]}")
    print("PASS runtime isolation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
