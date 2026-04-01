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

- `config/project-instance.json` with the runtime repo URL and derived GitHub owner/repo slug
- GitHub Issue polling intake config with a per-instance cursor path
- Manual Brief intake inbox/archive directories
- Conservative but configurable runtime defaults for parallel tasks and active worktrees

## What `start` does

- Marks the instance as `running` in `state/runtime.json`
- Ensures GitHub issue cursor state exists
- Exposes the active intake targets and worktree paths for downstream harness/poller work
