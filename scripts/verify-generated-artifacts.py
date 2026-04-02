#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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
        runtime_root = temp_root / "runtime"
        bootstrap_install = subprocess.run(
            ["bash", str(repo_root / "scripts" / "bootstrap-host-runtime.sh"), "install", "--dry-run", "--json", "--runtime-root", str(runtime_root)],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "CLAWHOST_PRESENT_TOOLS": "git,tmux,python3",
                "CLAWHOST_MISSING_TOOLS": "node,uv,gh,openclaw,clawteam",
                "OPENCLAW_INSTALL_CMD": "echo install-openclaw-placeholder",
                "CLAWTEAM_INSTALL_CMD": "echo install-clawteam-placeholder",
            },
        )
        (artifacts_root / "bootstrap-install.json").write_text(bootstrap_install.stdout)

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
        subprocess.run(
            [
                "python3",
                str(repo_root / "scripts" / "clawhost-instance.py"),
                "start",
                "--instances-root",
                str(instances_root),
                "--name",
                args.instance_name,
            ],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        describe = subprocess.run(
            [
                "python3",
                str(repo_root / "scripts" / "clawhost-instance.py"),
                "describe",
                "--instances-root",
                str(instances_root),
                "--name",
                args.instance_name,
            ],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        (artifacts_root / "instance-describe.json").write_text(describe.stdout)

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
