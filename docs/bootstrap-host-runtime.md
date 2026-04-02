# Bootstrap Host Runtime

`scripts/bootstrap-host-runtime.sh` prepares the shared host runtime used by Clawhost Kit.

It answers one narrow question: **is this host ready to run the shared Clawhost runtime, and if not, what can the repo safely do for you?**

## Covered dependencies

- `git`
- `tmux`
- `node`
- `python3`
- `uv`
- `gh`
- `openclaw` (host-specific install command via `OPENCLAW_INSTALL_CMD`)
- `clawteam` (host-specific install command via `CLAWTEAM_INSTALL_CMD`)

## What the bootstrap script owns vs. what the operator still owns

The script owns:

- runtime-root directory creation (`bin/`, `instances/`, `logs/`, `cache/`)
- dependency inspection for the supported tool list
- safe built-in installs for tools it knows how to install through `apt-get` or `brew`
- execution of your explicit `OPENCLAW_INSTALL_CMD` / `CLAWTEAM_INSTALL_CMD`

The operator still owns:

- the exact install commands for `openclaw` and `clawteam`
- any package-manager override when autodetection is wrong or unavailable
- auth/bootstrap steps outside this repo (for example GitHub auth or OpenClaw auth)
- long-running service wiring such as systemd units, launchd jobs, or reverse proxies

This split is intentional: the repo bootstraps a host runtime layout, but it does **not** guess production-specific service wiring.

## Command modes and what to expect

| Command | Changes host state? | Primary purpose | Important output |
| --- | --- | --- | --- |
| `plan --json` | No | Show the full dependency/install plan | tool statuses, built-in install commands, manual hints |
| `check --json` | No | Fail fast if anything is not already present | same JSON payload as `plan`, but exits non-zero if any tool is not `present` |
| `install --dry-run` | No | Preview the directory creation and installer commands | `DRY RUN ...` lines for each directory/install action |
| `install` | Yes | Create runtime layout and run installs | real `mkdir` plus install commands/hints |

## Status meanings in `plan` / `check`

Each tool is reported as one of:

- `present` — already available on `PATH`
- `missing` — not installed, but the script has a concrete install command or install command env var available
- `manual` — not installed and the script can only tell you what to provide next

For `openclaw` and `clawteam` specifically:

- before you export `OPENCLAW_INSTALL_CMD` / `CLAWTEAM_INSTALL_CMD`, they usually appear as `manual`
- after you export those env vars, they appear as `missing` until the tools are actually installed
- `check` only passes when every tool is `present`

That means `check --json` is a **readiness gate**, not a planning step.

## Operator decisions before install

Before you run a real install, decide these four things explicitly:

1. **Runtime root** — default is `/opt/clawhost`; this repo examples commonly use `/srv/clawhost`
2. **Package manager path** — let the script autodetect `brew`/`apt-get`, or pin `--package-manager manual` / another supported value when needed
3. **`openclaw` and `clawteam` installer commands** — export the exact commands your host should run
4. **Post-bootstrap service model** — decide how polling/gateway processes will be supervised after bootstrap, because this repo does not yet create those services for you

## Recommended operator sequence

### 1. Inspect the plan first

```bash
scripts/bootstrap-host-runtime.sh plan --json
```

Use this to answer:

- which tools are already available
- which tools the script can install directly
- which tools still need a manual decision from you

### 2. Decide host-specific install commands

If `openclaw` and `clawteam` are not already installed, export commands that are correct for **your** host:

```bash
export OPENCLAW_INSTALL_CMD='<your host-specific openclaw install command>'
export CLAWTEAM_INSTALL_CMD='<your host-specific clawteam install command>'
```

The repo intentionally does not ship guessed defaults here.

### 3. Dry-run the install

```bash
scripts/bootstrap-host-runtime.sh install --dry-run --runtime-root /srv/clawhost
```

Confirm that:

- the runtime root is correct
- the install commands are the ones you intended
- nothing surprising would be executed

### 4. Run the real install

```bash
scripts/bootstrap-host-runtime.sh install --runtime-root /srv/clawhost
```

### 5. Re-run the readiness check

```bash
scripts/bootstrap-host-runtime.sh check --json
```

If this still reports non-`present` tools, finish the remaining manual steps before moving on to instance creation.

If you want a Linux/systemd starting point for the next step, use:

- `examples/services/systemd/clawhost-instance.env.example`
- `examples/services/systemd/clawhost-instance-bootstrap@.service`

These assets intentionally cover only bootstrap + instance create/start. They do not define a full polling daemon or gateway topology for you.

## Usage

```bash
scripts/bootstrap-host-runtime.sh plan --json
scripts/bootstrap-host-runtime.sh check --json
scripts/bootstrap-host-runtime.sh install --dry-run --runtime-root /tmp/clawhost
```

The script auto-detects `brew` or `apt-get`. For `gh`, `openclaw`, and `clawteam`, it emits install hints when no safe built-in installer is available.
