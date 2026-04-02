import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "verify-generated-artifacts.py"


class VerifyGeneratedArtifactsTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )

    def test_script_writes_bootstrap_and_describe_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir) / "artifacts"
            repo_url = "https://github.com/example-org/runtime-proof"
            result = self.run_script(
                "--repo-url",
                repo_url,
                "--artifacts-dir",
                str(artifacts),
                "--instance-name",
                "runtime-proof",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            bootstrap_install = json.loads((artifacts / "bootstrap-install.json").read_text())
            describe = json.loads((artifacts / "instance-describe.json").read_text())

            self.assertEqual(bootstrap_install["dry_run"], True)
            self.assertTrue(any(path.endswith("/runtime/services") for path in bootstrap_install["created_directories"]))
            self.assertEqual(describe["instance_id"], "runtime-proof")
            self.assertEqual(describe["repo"]["url"], repo_url)
            self.assertTrue(describe["paths"]["config_file"].endswith("/instances/runtime-proof/config/project-instance.json"))
            self.assertTrue(describe["runtime"]["cursor_path"].endswith("/instances/runtime-proof/state/github-issue-cursor.json"))


if __name__ == "__main__":
    unittest.main()
