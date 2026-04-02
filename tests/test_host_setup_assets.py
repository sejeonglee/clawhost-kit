import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICE_TEMPLATE = REPO_ROOT / "examples" / "services" / "systemd" / "clawhost-instance-bootstrap@.service"
ENV_TEMPLATE = REPO_ROOT / "examples" / "services" / "systemd" / "clawhost-instance.env.example"


class HostSetupAssetTests(unittest.TestCase):
    def test_systemd_unit_references_environment_file_and_bootstrap_commands(self):
        content = SERVICE_TEMPLATE.read_text()

        self.assertIn("EnvironmentFile=/etc/clawhost/%i.env", content)
        self.assertIn("scripts/bootstrap-host-runtime.sh install --runtime-root \"$CLAWHOST_RUNTIME_ROOT\"", content)
        self.assertIn("python3 scripts/clawhost-instance.py create", content)
        self.assertIn("python3 scripts/clawhost-instance.py start", content)
        self.assertIn("if [[ ! -f \"$config_path\" ]]; then", content)

    def test_env_template_contains_required_operator_inputs(self):
        content = ENV_TEMPLATE.read_text()

        for expected in (
            "CLAWHOST_REPO_ROOT=",
            "CLAWHOST_RUNTIME_ROOT=",
            "CLAWHOST_INSTANCES_ROOT=",
            "CLAWHOST_INSTANCE_NAME=",
            "CLAWHOST_REPO_URL=",
            "OPENCLAW_INSTALL_CMD=",
            "CLAWTEAM_INSTALL_CMD=",
        ):
            self.assertIn(expected, content)


if __name__ == "__main__":
    unittest.main()
