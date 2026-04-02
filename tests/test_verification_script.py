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
            repo_url = "git@github.com:example-org/runtime-proof.git"
            result = self.run_script(
                "--dry-run",
                "--repo-url",
                repo_url,
                "--artifacts-dir",
                tmpdir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["repo_url"], repo_url)
            self.assertEqual(
                payload["repo_url_injection"]["forwarded_to"],
                ["generated-artifact-validation", "docker-harness-dry-run", "docker-harness-live"],
            )
            labels = [step["label"] for step in payload["steps"]]
            self.assertEqual(labels[:3], ["unit-tests", "python-compile", "bash-syntax"])
            self.assertIn("generated-artifact-validation", labels)
            self.assertIn("docker-harness-dry-run", labels)
            self.assertIn("docker-harness-live", labels)
            self.assertEqual(payload["artifacts_dir"], tmpdir)
            forwarded = [step for step in payload["steps"] if "--repo-url" in step["command"]]
            self.assertEqual(len(forwarded), 3)
            for step in forwarded:
                self.assertIn(repo_url, step["command"])

    def test_summary_includes_generated_and_docker_artifacts_from_new_surfaces(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir)
            (artifacts / "unit-tests.log").write_text("ok\n")
            docker_dir = artifacts / "docker-harness"
            docker_dir.mkdir()
            for name in ("bootstrap-install.json", "instance-describe.json", "summary.json"):
                (docker_dir / name).write_text("{}\n")
            generated_dir = artifacts / "generated-artifact-validation"
            generated_dir.mkdir()
            for name in ("bootstrap-install.json", "instance-describe.json"):
                (generated_dir / name).write_text("{}\n")

            summary_command = r"""
artifacts_dir="$1"
repo_url="$2"
python3 - <<PY
import json
from pathlib import Path
artifacts = Path(r'''$artifacts_dir''')
summary = {
    'repo_url': r'''$repo_url''',
    'artifacts_dir': str(artifacts),
    'logs': sorted(p.name for p in artifacts.glob('*.log')),
    'docker_artifacts': sorted(p.name for p in (artifacts / 'docker-harness').glob('*')),
    'generated_artifacts': sorted(p.name for p in (artifacts / 'generated-artifact-validation').glob('*')),
}
print(json.dumps(summary))
PY
"""
            result = subprocess.run(
                ["bash", "-lc", summary_command, "bash", str(artifacts), "https://github.com/example-org/runtime-proof"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("bootstrap-install.json", payload["docker_artifacts"])
            self.assertIn("instance-describe.json", payload["docker_artifacts"])
            self.assertIn("bootstrap-install.json", payload["generated_artifacts"])
            self.assertIn("instance-describe.json", payload["generated_artifacts"])


if __name__ == "__main__":
    unittest.main()
