#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.runtime_isolation import build_task_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and validate real instance artifacts.")
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument("--instance-name", default="verification-instance")
    parser.add_argument("--host-defaults-ref", default="clawhost-dev-01")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    artifacts_root = Path(args.artifacts_dir)
    artifacts_root.mkdir(parents=True, exist_ok=True)

    temp_root = Path(tempfile.mkdtemp(prefix="clawhost-verify-"))
    try:
        instances_root = temp_root / "instances"
        subprocess.run(
            [
                "python3",
                str(repo_root / "scripts" / "clawhost-instance.py"),
                "create",
                "--instances-root",
                str(instances_root),
                "--name",
                args.instance_name,
                "--repo-url",
                args.repo_url,
                "--host-defaults-ref",
                args.host_defaults_ref,
            ],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

        project_path = instances_root / args.instance_name / "config" / "project-instance.json"
        project = json.loads(project_path.read_text())
        project_copy = artifacts_root / "project-instance.json"
        project_copy.write_text(json.dumps(project, indent=2) + "\n")

        task = build_task_fixture(project, task_id="verification-smoke")
        task_path = artifacts_root / "task-ephemeral.json"
        task_path.write_text(json.dumps(task, indent=2) + "\n")

        host_global = repo_root / "examples" / "config" / "host-global.json"
        subprocess.run(
            ["python3", str(repo_root / "tools" / "config_boundary.py"), str(host_global), str(project_copy), str(task_path)],
            cwd=repo_root,
            check=True,
        )
        subprocess.run(
            ["python3", str(repo_root / "tools" / "runtime_isolation.py"), str(host_global), str(project_copy), str(task_path)],
            cwd=repo_root,
            check=True,
        )
    finally:
        shutil.rmtree(temp_root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
