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
```

The script auto-detects `brew` or `apt-get`. For `gh`, `openclaw`, and `clawteam`, it emits install hints when no safe built-in installer is available.
