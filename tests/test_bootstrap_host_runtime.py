import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "bootstrap-host-runtime.sh"


class BootstrapHostRuntimeTests(unittest.TestCase):
    maxDiff = None

    def run_script(self, *args, env=None):
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            env=merged_env,
            text=True,
            capture_output=True,
        )

    def test_plan_json_for_apt_reports_expected_install_steps(self):
        result = self.run_script(
            "plan",
            "--json",
            "--package-manager",
            "apt-get",
            env={
                "CLAWHOST_PRESENT_TOOLS": "",
                "CLAWHOST_MISSING_TOOLS": "git,tmux,node,python3,uv,gh,openclaw,clawteam",
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(payload["package_manager"], "apt-get")
        steps = {step["id"]: step for step in payload["steps"]}

        self.assertEqual(steps["git"]["status"], "missing")
        self.assertEqual(steps["git"]["install"], ["sudo", "apt-get", "install", "-y", "git"])
        self.assertEqual(
            steps["python3"]["install"],
            ["sudo", "apt-get", "install", "-y", "python3", "python3-venv", "python3-pip"],
        )
        self.assertEqual(steps["uv"]["status"], "missing")
        self.assertIn("astral.sh/uv/install.sh", steps["uv"]["install_hint"])
        self.assertEqual(steps["gh"]["status"], "missing")
        self.assertIn("cli.github.com", steps["gh"]["install_hint"])
        self.assertEqual(steps["openclaw"]["status"], "manual")
        self.assertIn("OPENCLAW_INSTALL_CMD", steps["openclaw"]["install_hint"])
        self.assertEqual(steps["clawteam"]["status"], "manual")
        self.assertIn("CLAWTEAM_INSTALL_CMD", steps["clawteam"]["install_hint"])

    def test_check_json_succeeds_when_all_tools_present(self):
        result = self.run_script(
            "check",
            "--json",
            env={
                "CLAWHOST_PRESENT_TOOLS": "git,tmux,node,python3,uv,gh,openclaw,clawteam",
                "CLAWHOST_MISSING_TOOLS": "",
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["ready"], True)
        self.assertEqual(payload["summary"]["missing"], [])

    def test_install_dry_run_creates_runtime_root_layout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_root = Path(tmpdir) / "runtime"
            result = self.run_script(
                "install",
                "--dry-run",
                "--runtime-root",
                str(runtime_root),
                env={
                    "CLAWHOST_PRESENT_TOOLS": "git,tmux,node,python3,uv,gh",
                    "CLAWHOST_MISSING_TOOLS": "openclaw,clawteam",
                    "OPENCLAW_INSTALL_CMD": "echo install-openclaw",
                    "CLAWTEAM_INSTALL_CMD": "echo install-clawteam",
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY RUN mkdir -p", result.stdout)
            self.assertIn(str(runtime_root / "bin"), result.stdout)
            self.assertIn("DRY RUN echo install-openclaw", result.stdout)
            self.assertIn("DRY RUN echo install-clawteam", result.stdout)

    def test_install_json_reports_created_layout_and_tool_actions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_root = Path(tmpdir) / "runtime"
            result = self.run_script(
                "install",
                "--json",
                "--dry-run",
                "--runtime-root",
                str(runtime_root),
                "--package-manager",
                "apt-get",
                env={
                    "CLAWHOST_PRESENT_TOOLS": "git,tmux,node,python3",
                    "CLAWHOST_MISSING_TOOLS": "uv,gh,openclaw,clawteam",
                    "OPENCLAW_INSTALL_CMD": "echo install-openclaw",
                    "CLAWTEAM_INSTALL_CMD": "echo install-clawteam",
                },
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["runtime_root"], str(runtime_root))
            self.assertEqual(payload["package_manager"], "apt-get")
            self.assertEqual(payload["dry_run"], True)
            self.assertIn(str(runtime_root / "instances"), payload["created_directories"])
            self.assertIn(str(runtime_root / "services"), payload["created_directories"])

            actions = {step["id"]: step for step in payload["tool_actions"]}
            self.assertEqual(actions["git"]["status"], "present")
            self.assertEqual(actions["uv"]["status"], "missing")
            self.assertIn("astral.sh/uv/install.sh", actions["uv"]["install_hint"])
            self.assertEqual(actions["openclaw"]["command"], "echo install-openclaw")
            self.assertEqual(actions["clawteam"]["command"], "echo install-clawteam")


if __name__ == "__main__":
    unittest.main()
