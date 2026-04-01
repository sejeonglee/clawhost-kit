#!/usr/bin/env python3
"""Validate clawhost-kit config scope boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCOPE_RULES = {
    "host-global": {
        "required": {"host_id", "paths", "toolchain", "concurrency", "resources", "secret_refs", "logging"},
        "allowed": {"scope", "host_id", "paths", "toolchain", "concurrency", "resources", "secret_refs", "logging"},
        "forbidden": {"repo", "poller", "instance_id", "task_id", "worktree", "execution", "artifacts", "source_ref"},
    },
    "project-instance": {
        "required": {"instance_id", "repo", "paths", "intake", "poller", "host_defaults_ref", "runtime_overrides", "env"},
        "allowed": {"scope", "instance_id", "created_at", "repo", "paths", "intake", "poller", "host_defaults_ref", "runtime_overrides", "env"},
        "forbidden": {"host_id", "concurrency", "resources", "secret_refs", "task_id", "worktree", "execution", "artifacts", "source_ref"},
    },
    "per-task-ephemeral": {
        "required": {"task_id", "instance_id", "source_ref", "worktree", "execution", "artifacts"},
        "allowed": {"scope", "task_id", "instance_id", "source_ref", "worktree", "execution", "artifacts"},
        "forbidden": {"host_id", "repo", "poller", "concurrency", "resources", "secret_refs", "logging", "intake", "host_defaults_ref", "runtime_overrides"},
    },
}

SECRETISH_KEYS = {"token", "secret", "password", "api_key"}


class ValidationError(Exception):
    """Raised when a config file violates the boundary."""


def load_config(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: top-level JSON value must be an object")
    return data


def _contains_secret_like_key(value: Any, scope: str, path: tuple[str, ...] = ()) -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = key.lower()
            current_path = path + (key,)
            if scope != "host-global" and any(marker in lowered for marker in SECRETISH_KEYS):
                violations.append(".".join(current_path))
            violations.extend(_contains_secret_like_key(nested, scope, current_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            violations.extend(_contains_secret_like_key(nested, scope, path + (str(index),)))
    return violations


def validate_config(data: dict[str, Any], source: str = "<memory>") -> None:
    scope = data.get("scope")
    if scope not in SCOPE_RULES:
        valid = ", ".join(sorted(SCOPE_RULES))
        raise ValidationError(f"{source}: scope must be one of {valid}")

    rule = SCOPE_RULES[scope]
    keys = set(data)
    missing = sorted(rule["required"] - keys)
    extra = sorted(keys - rule["allowed"])
    forbidden = sorted(keys & rule["forbidden"])

    errors: list[str] = []
    if missing:
        errors.append(f"missing required keys: {', '.join(missing)}")
    if extra:
        errors.append(f"unexpected keys for {scope}: {', '.join(extra)}")
    if forbidden:
        errors.append(f"cross-scope keys not allowed in {scope}: {', '.join(forbidden)}")

    secret_violations = _contains_secret_like_key(data, scope)
    if secret_violations:
        errors.append(
            "secret-like keys are only allowed in host-global secret_refs: " + ", ".join(secret_violations)
        )

    if errors:
        raise ValidationError(f"{source}: " + "; ".join(errors))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python3 tools/config_boundary.py <config.json> [<config.json> ...]", file=sys.stderr)
        return 2

    failed = False
    for raw_path in argv[1:]:
        path = Path(raw_path)
        try:
            data = load_config(path)
            validate_config(data, source=str(path))
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            failed = True
            print(f"FAIL {exc}", file=sys.stderr)
        else:
            print(f"PASS {path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
