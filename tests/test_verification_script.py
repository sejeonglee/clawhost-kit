import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run-verification.sh"


class VerificationScriptTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )

    def test_dry_run_lists_core_and_docker_steps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_script(
                "--dry-run",
                "--repo-url",
                "https://github.com/sejeonglee/llm-report-module",
                "--artifacts-dir",
                tmpdir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["repo_url"], "https://github.com/sejeonglee/llm-report-module")
            labels = [step["label"] for step in payload["steps"]]
            self.assertEqual(labels[:3], ["unit-tests", "python-compile", "bash-syntax"])
            self.assertIn("generated-artifact-validation", labels)
            self.assertIn("docker-harness-dry-run", labels)
            self.assertIn("docker-harness-live", labels)
            self.assertEqual(payload["artifacts_dir"], tmpdir)


if __name__ == "__main__":
    unittest.main()
