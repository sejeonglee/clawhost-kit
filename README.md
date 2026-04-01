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
