# Config Boundary

`clawhost-kit` separates persisted state into three scopes:

1. **host-global** — shared host runtime and fleet-wide limits.
2. **project-instance** — one repo-backed instance with repo/poller/runtime settings.
3. **per-task-ephemeral** — one execution lane for a single task/worktree run.

The boundary is intentionally strict so later lifecycle scripts can read the smallest possible surface:

- **host-global** owns shared tool/runtime paths, concurrency caps, resource sizing knobs, and secret references.
- **project-instance** owns repo URL, intake/poller settings, instance-local filesystem roots, and references back to host-global defaults.
- **per-task-ephemeral** owns only task-run state such as branch/worktree/artifact paths and execution timestamps.

## Scope Rules

### 1. Host-global
Persist once per host. Safe to share across instances.

Allowed responsibilities:
- host identity and install roots
- shared runtime/toolchain configuration
- host-wide concurrency caps
- host-wide resource policy knobs
- default secret reference names
- logging/observability defaults

Must **not** contain:
- repo-specific URLs
- poller cursors for a repo
- task execution state, worktrees, or branch names

### Host-global scaling knobs
The host-global layer is where capacity policy lives. Conservative defaults can target a small host, but scale-up is a config-only change.

Recommended knobs:
- `concurrency.max_active_instances`
- `concurrency.max_parallel_tasks`
- `resources.host_memory_gb`
- `resources.reserved_memory_gb`
- `resources.max_memory_per_instance_gb`
- `resources.max_memory_per_task_gb`
- `resources.scale_profile`

Example scaling guidance:
- small host default: `host_memory_gb=8`, `reserved_memory_gb=2`, `max_active_instances=3`, `max_parallel_tasks=1`
- future 24GB host: increase these knobs (for example `host_memory_gb=24`, `reserved_memory_gb=4`, `max_active_instances=6`, `max_parallel_tasks=2`) without changing instance/task schemas

### 2. Project-instance
Persist once per managed repository instance.

Allowed responsibilities:
- instance identifier and repo URL
- per-repo poller configuration and cursors
- instance-local directories
- intake source selection (`github_issue`, `manual_brief`)
- overrides that stay inside the instance boundary
- references to host-global defaults/secrets by name only

Must **not** contain:
- raw host secrets or host-global concurrency/resource policy
- per-task worktree state
- branch names for active executions

### 3. Per-task-ephemeral
Persist once per task execution lane.

Allowed responsibilities:
- task id / issue id linkage
- execution branch and worktree paths
- status timestamps and exit metadata
- artifact paths produced by the run

Must **not** contain:
- repo poller settings or repo cursor state
- host-global runtime/resource configuration
- raw secrets

## Encoded Guardrails

This repo encodes the boundary in `tools/config_boundary.py`:

- strict top-level allow-lists per scope
- required keys per scope
- cross-scope forbidden keys that catch leakage
- secret-like field bans outside host-global secret references

Validate a file:

```bash
python3 tools/config_boundary.py examples/config/host-global.json
python3 tools/config_boundary.py examples/config/project-instance.json
python3 tools/config_boundary.py examples/config/task-ephemeral.json
```

Validate all bundled examples:

```bash
python3 tools/config_boundary.py \
  examples/config/host-global.json \
  examples/config/project-instance.json \
  examples/config/task-ephemeral.json
```
