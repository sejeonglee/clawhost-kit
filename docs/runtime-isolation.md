# Runtime Isolation Model

This package keeps each managed repository inside its own instance boundary while still allowing one host to supervise multiple instances.

## Isolation Rules

### Host-global caps
Host-global config sets shared admission limits:
- `concurrency.max_active_instances`
- `concurrency.max_parallel_tasks`

These caps are the only place where fleet-wide execution limits are stored.
Project-instance and per-task state may observe these limits, but they may not redefine them.

### Project-instance isolation
Each repository instance owns a private subtree:

- `paths.instance_root`
- `paths.state_root`
- `paths.worktrees_root`
- `poller.cursor_file`

Required invariants:
- `state_root` must live under `instance_root`
- `worktrees_root` must live under `instance_root`
- `poller.cursor_file` must live under `state_root`
- poller state is per-instance, never host-global and never per-task

### Per-task isolation
Each execution lane lives under a single project-instance:

- `task.instance_id` must match the project-instance id
- `worktree.path` must live under the instance `worktrees_root`
- task artifacts/logs must live under the instance `state_root`
- task state can reference a source issue/brief, but it must not carry poller cursor state

## Encoded Guardrails

`tools/runtime_isolation.py` validates the cross-file invariants between:

1. one host-global config
2. one project-instance config
3. one per-task-ephemeral config

Example:

```bash
python3 tools/runtime_isolation.py \
  examples/config/host-global.json \
  examples/config/project-instance.json \
  examples/config/task-ephemeral.json
```

Successful validation proves:
- host-wide concurrency caps are defined centrally
- per-instance poller/state/worktree paths are nested inside one instance root
- task worktrees/artifacts stay inside the owning instance boundary
