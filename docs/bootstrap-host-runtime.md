# Bootstrap Host Runtime

`scripts/bootstrap-host-runtime.sh` prepares the shared host runtime used by Clawhost Kit.

## Covered dependencies

- `git`
- `tmux`
- `node`
- `python3`
- `uv`
- `gh`
- `openclaw` (host-specific install command via `OPENCLAW_INSTALL_CMD`)
- `clawteam` (host-specific install command via `CLAWTEAM_INSTALL_CMD`)

## Usage

```bash
scripts/bootstrap-host-runtime.sh plan --json
scripts/bootstrap-host-runtime.sh check --json
scripts/bootstrap-host-runtime.sh install --dry-run --runtime-root /tmp/clawhost
scripts/bootstrap-host-runtime.sh install --dry-run --json --runtime-root /tmp/clawhost
```

The script auto-detects `brew` or `apt-get`. For `gh`, `openclaw`, and `clawteam`, it emits install hints when no safe built-in installer is available.

`install --dry-run --json` is the most complete operator-facing report. It includes:

- `runtime_root`
- `created_directories`
- `tool_actions` with package-manager installs or manual-install hints

The install layout now reserves shared host directories for:

- `bin`
- `instances`
- `logs`
- `cache`
- `env`
- `services`
