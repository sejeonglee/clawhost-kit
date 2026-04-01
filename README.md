# Clawhost Kit

Bootstrap host kit for multi-project ClawTeam/OpenClaw instances.

## Host runtime bootstrap

Use `scripts/bootstrap-host-runtime.sh` to inspect, validate, or dry-run installation of the shared host runtime dependencies:

```bash
scripts/bootstrap-host-runtime.sh plan --json
scripts/bootstrap-host-runtime.sh check --json
scripts/bootstrap-host-runtime.sh install --dry-run --runtime-root /tmp/clawhost
```

See `docs/bootstrap-host-runtime.md` for the dependency matrix and override knobs.

## Project instance lifecycle

Use `scripts/clawhost-instance.py` to create, start, and inspect a repo-backed project instance with GitHub Issue polling and Manual Brief intake:

```bash
python3 scripts/clawhost-instance.py create --instances-root /srv/clawhost/instances --name report-module --repo-url https://github.com/sejeonglee/llm-report-module
python3 scripts/clawhost-instance.py start --instances-root /srv/clawhost/instances --name report-module
python3 scripts/clawhost-instance.py status --instances-root /srv/clawhost/instances --name report-module
```

See `docs/project-instance-lifecycle.md` for the instance layout and default runtime knobs.
