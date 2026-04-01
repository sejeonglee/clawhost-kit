import json
import tempfile
import unittest
from pathlib import Path

from tools.config_boundary import ValidationError, load_config, validate_config


class ConfigBoundaryTests(unittest.TestCase):
    def _load_example(self, name: str):
        path = Path("examples/config") / name
        return load_config(path)

    def test_examples_are_valid(self):
        for name in [
            "host-global.json",
            "project-instance.json",
            "task-ephemeral.json",
        ]:
            with self.subTest(name=name):
                validate_config(self._load_example(name), source=name)

    def test_project_instance_rejects_host_global_keys(self):
        config = self._load_example("project-instance.json")
        config["concurrency"] = {"max_parallel_tasks": 2}

        with self.assertRaises(ValidationError) as error:
            validate_config(config, source="project-instance.json")

        self.assertIn("cross-scope keys not allowed", str(error.exception))

    def test_task_scope_rejects_repo_poller_state(self):
        config = self._load_example("task-ephemeral.json")
        config["poller"] = {"interval_seconds": 10}

        with self.assertRaises(ValidationError) as error:
            validate_config(config, source="task-ephemeral.json")

        self.assertIn("poller", str(error.exception))

    def test_non_host_scope_rejects_secret_like_keys(self):
        config = self._load_example("project-instance.json")
        config["env"]["github_token"] = "ghp_example"

        with self.assertRaises(ValidationError) as error:
            validate_config(config, source="project-instance.json")

        self.assertIn("secret-like keys", str(error.exception))

    def test_load_config_requires_object_top_level(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(json.dumps(["not", "an", "object"]))

            with self.assertRaises(ValidationError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
