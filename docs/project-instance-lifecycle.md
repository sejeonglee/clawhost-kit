# Project Instance Lifecycle

`scripts/clawhost-instance.py` provides the repo-URL-driven instance lifecycle surface for Clawhost Kit.

## Commands

```bash
python3 scripts/clawhost-instance.py create \
  --instances-root /srv/clawhost/instances \
  --name report-module \
  --repo-url https://github.com/sejeonglee/llm-report-module

python3 scripts/clawhost-instance.py start --instances-root /srv/clawhost/instances --name report-module
python3 scripts/clawhost-instance.py status --instances-root /srv/clawhost/instances --name report-module
```

## What `create` materializes

- `config/project-instance.json` matching the canonical `project-instance` schema
- GitHub Issue polling intake config with a per-instance cursor file
- Manual Brief intake inbox/archive directories
- Conservative but configurable instance-local runtime overrides for parallel tasks and active worktrees

## Canonical generated schema

`create` emits a `project-instance` document with these top-level keys:

- `scope`
- `instance_id`
- `created_at`
- `repo`
- `paths`
- `intake`
- `poller`
- `host_defaults_ref`
- `runtime_overrides`
- `env`

## What `start` does

- Marks the instance as `running` in `state/runtime.json`
- Ensures GitHub issue cursor state exists
- Exposes the active intake targets and worktree paths for downstream harness/poller work

## Verification expectations

Generated instance artifacts should validate with:

```bash
python3 tools/config_boundary.py \
  examples/config/host-global.json \
  /path/to/generated/project-instance.json \
  /path/to/generated/task-ephemeral.json

python3 tools/runtime_isolation.py \
  examples/config/host-global.json \
  /path/to/generated/project-instance.json \
  /path/to/generated/task-ephemeral.json
```
