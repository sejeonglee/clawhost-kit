import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "clawhost-instance.py"


class InstanceLifecycleTests(unittest.TestCase):
    maxDiff = None

    def run_script(self, *args):
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )

    def test_create_materializes_instance_with_github_issue_and_manual_brief_targets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "instances"
            result = self.run_script(
                "create",
                "--instances-root",
                str(root),
                "--name",
                "reporting",
                "--repo-url",
                "https://github.com/sejeonglee/llm-report-module",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            config_path = root / "reporting" / "config" / "project-instance.json"
            config = json.loads(config_path.read_text())

            self.assertEqual(payload["instance_name"], "reporting")
            self.assertEqual(config["repo"]["url"], "https://github.com/sejeonglee/llm-report-module")
            self.assertEqual(config["repo"]["github_owner"], "sejeonglee")
            self.assertEqual(config["repo"]["github_repo"], "llm-report-module")
            self.assertEqual(config["intake"]["github_issue_polling"]["enabled"], True)
            self.assertEqual(config["intake"]["manual_brief"]["enabled"], True)
            self.assertEqual(config["runtime_defaults"]["max_parallel_tasks"], 2)
            self.assertTrue((root / "reporting" / "intake" / "manual-briefs").is_dir())
            self.assertTrue((root / "reporting" / "worktrees").is_dir())

    def test_start_marks_instance_running_and_status_reports_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "instances"
            self.run_script(
                "create",
                "--instances-root",
                str(root),
                "--name",
                "reporting",
                "--repo-url",
                "git@github.com:sejeonglee/llm-report-module.git",
                "--poll-interval-seconds",
                "180",
                "--max-parallel-tasks",
                "3",
            )

            start = self.run_script(
                "start",
                "--instances-root",
                str(root),
                "--name",
                "reporting",
            )
            self.assertEqual(start.returncode, 0, start.stderr)
            start_payload = json.loads(start.stdout)
            self.assertEqual(start_payload["status"], "running")
            self.assertEqual(start_payload["poll_interval_seconds"], 180)
            self.assertEqual(start_payload["max_parallel_tasks"], 3)

            runtime_state = json.loads((root / "reporting" / "state" / "runtime.json").read_text())
            self.assertEqual(runtime_state["status"], "running")
            self.assertEqual(runtime_state["intake_sources"], ["github_issue_polling", "manual_brief"])
            self.assertTrue((root / "reporting" / "state" / "github-issues-cursor.json").is_file())

            status = self.run_script(
                "status",
                "--instances-root",
                str(root),
                "--name",
                "reporting",
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            status_payload = json.loads(status.stdout)
            self.assertEqual(status_payload["status"], "running")
            self.assertEqual(status_payload["repo_slug"], "sejeonglee/llm-report-module")
            self.assertEqual(status_payload["manual_brief_dir"], str(root / "reporting" / "intake" / "manual-briefs"))


if __name__ == "__main__":
    unittest.main()
