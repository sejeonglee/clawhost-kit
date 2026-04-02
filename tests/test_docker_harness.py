import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run-docker-harness.sh"


class DockerHarnessTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )

    def test_dry_run_renders_runtime_repo_url_and_artifact_mount(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir) / "artifacts"
            repo_url = "https://github.com/example-org/runtime-proof"
            result = self.run_script(
                "--dry-run",
                "--repo-url",
                repo_url,
                "--artifacts-dir",
                str(artifacts),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["repo_url"], repo_url)
            self.assertEqual(payload["repo_url_injection"]["phase"], "runtime")
            self.assertEqual(payload["repo_url_injection"]["mechanism"], "docker-run-env")
            self.assertEqual(payload["repo_url_injection"]["env_var"], "REPO_URL")
            self.assertTrue(payload["dockerfile"].endswith("docker/harness.Dockerfile"))
            self.assertIn("-e", payload["run_command"])
            self.assertIn(f"REPO_URL={repo_url}", payload["run_command"])
            self.assertTrue(any(str(artifacts) in part for part in payload["run_command"]))
            self.assertIn("clawhost-harness:local", payload["build_command"])
            self.assertFalse(any(repo_url in part for part in payload["build_command"]))

    def test_harness_dockerfile_does_not_bake_target_repo_url(self):
        dockerfile = (REPO_ROOT / "docker" / "harness.Dockerfile").read_text()
        self.assertNotIn("llm-report-module", dockerfile)
        self.assertIn("COPY . /workspace", dockerfile)

    def test_harness_entrypoint_validates_generated_config(self):
        entrypoint = (REPO_ROOT / "docker" / "harness-entrypoint.sh").read_text()
        self.assertIn("generated-project-instance.json", entrypoint)
        self.assertIn("generated-task-ephemeral.json", entrypoint)
        self.assertIn("tools/config_boundary.py", entrypoint)
        self.assertIn("tools/runtime_isolation.py", entrypoint)


if __name__ == "__main__":
    unittest.main()
