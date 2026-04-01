import unittest
from pathlib import Path

from tools.config_boundary import load_config
from tools.runtime_isolation import IsolationError, validate_runtime_isolation


class RuntimeIsolationTests(unittest.TestCase):
    def _load(self, name: str):
        return load_config(Path("examples/config") / name)

    def test_example_suite_is_isolated(self):
        validate_runtime_isolation(
            self._load("host-global.json"),
            self._load("project-instance.json"),
            self._load("task-ephemeral.json"),
        )

    def test_task_must_match_project_instance(self):
        task = self._load("task-ephemeral.json")
        task["instance_id"] = "another-instance"

        with self.assertRaises(IsolationError) as error:
            validate_runtime_isolation(
                self._load("host-global.json"),
                self._load("project-instance.json"),
                task,
            )

        self.assertIn("does not match", str(error.exception))

    def test_poller_cursor_must_live_under_state_root(self):
        project = self._load("project-instance.json")
        project["poller"]["cursor_file"] = "/srv/clawhost/shared/cursor.json"

        with self.assertRaises(IsolationError) as error:
            validate_runtime_isolation(
                self._load("host-global.json"),
                project,
                self._load("task-ephemeral.json"),
            )

        self.assertIn("poller.cursor_file", str(error.exception))

    def test_task_worktree_must_live_under_instance_worktrees_root(self):
        task = self._load("task-ephemeral.json")
        task["worktree"]["path"] = "/srv/clawhost/shared/worktrees/issue-42"

        with self.assertRaises(IsolationError) as error:
            validate_runtime_isolation(
                self._load("host-global.json"),
                self._load("project-instance.json"),
                task,
            )

        self.assertIn("worktree.path", str(error.exception))

    def test_host_caps_must_fit_available_memory(self):
        host = self._load("host-global.json")
        host["concurrency"]["max_parallel_tasks"] = 4

        with self.assertRaises(IsolationError) as error:
            validate_runtime_isolation(
                host,
                self._load("project-instance.json"),
                self._load("task-ephemeral.json"),
            )

        self.assertIn("max_parallel_tasks", str(error.exception))

    def test_reserved_memory_must_be_smaller_than_host(self):
        host = self._load("host-global.json")
        host["resources"]["reserved_memory_gb"] = 8

        with self.assertRaises(IsolationError) as error:
            validate_runtime_isolation(
                host,
                self._load("project-instance.json"),
                self._load("task-ephemeral.json"),
            )

        self.assertIn("reserved_memory_gb", str(error.exception))


if __name__ == "__main__":
    unittest.main()
