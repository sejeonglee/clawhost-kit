# Clawhost Kit

Clawhost Kit is a **host bootstrap + project-instance package** for running a shared OpenClaw/ClawTeam environment on one host.

It is designed for this operating model:
- **shared host runtime**
- **repo URL provided at runtime**
- **one project instance per repo**
- **GitHub Issue polling + Manual Brief intake**
- **Docker harness for isolated end-to-end verification**

It does **not** bake the target repo into the image. The repo URL is always injected at runtime.

---

# Can I start setting this up right now?

**Yes.**

If you clone this repository onto a host that has at least:
- `bash`
- `python3`
- `git`

then you can start the setup flow immediately.

For the full local + Docker verification flow used in this repo, you should also have:
- `docker`

For real host bootstrap/install, the package can plan/check/install around:
- `git`
- `tmux`
- `node`
- `python3`
- `uv`
- `gh`
- `openclaw`
- `clawteam`

The only important caveat is this:
- `openclaw` and `clawteam` do **not** have hardcoded installer commands in this repo.
- You are expected to provide host-appropriate install commands through environment variables when you want bootstrap to install them automatically.

That means the package is **usable now**, but the exact install commands for OpenClaw/ClawTeam must match your real target host.

---

# What this package contains

## 1. Host runtime bootstrap
Use `scripts/bootstrap-host-runtime.sh` to:
- inspect what the host is missing
- produce an install plan
- run install commands or dry-run them
- create the host runtime root layout

## 2. Project instance lifecycle
Use `scripts/clawhost-instance.py` to:
- create a project instance from a repo URL
- initialize project-specific config/state/worktree paths
- mark the instance running
- inspect instance runtime state

## 3. Config boundary validation
Use:
- `tools/config_boundary.py`
- `tools/runtime_isolation.py`
- `scripts/verify-generated-artifacts.py`

to validate the separation between:
- **host-global** config
- **project-instance** config
- **per-task ephemeral** state

## 4. Docker test harness
Use:
- `docker/harness.Dockerfile`
- `docker/harness-entrypoint.sh`
- `scripts/run-docker-harness.sh`

to validate the package in a disposable container without baking the target repo into the image.

## 5. Consolidated verification
Use `scripts/run-verification.sh` to run:
- unit tests
- python compile checks
- bash syntax checks
- docker harness dry-run
- docker harness live execution

---

# Repository layout

```text
.
├── docker/
├── docs/
├── examples/
├── scripts/
├── tests/
├── tools/
└── README.md
```

Key files:
- `scripts/bootstrap-host-runtime.sh`
- `scripts/clawhost-instance.py`
- `scripts/run-docker-harness.sh`
- `scripts/run-verification.sh`
- `tools/config_boundary.py`
- `tools/runtime_isolation.py`

---

# Recommended setup flow on a fresh host

## Step 0. Clone this repo

```bash
git clone <THIS-REPO-URL> clawhost-kit
cd clawhost-kit
```

If this repo has not been pushed to a remote yet, you can clone/copy it by whatever internal method you use, but from this point onward the commands are the same.

---

## Step 1. Inspect the host bootstrap plan

```bash
scripts/bootstrap-host-runtime.sh plan --json
```

This tells you:
- which tools are already present
- which tools are missing
- which tools only have hints/manual install behavior

If you want a hard pass/fail readiness check:

```bash
scripts/bootstrap-host-runtime.sh check --json
```

Notes:
- `plan` always reports.
- `check` exits non-zero if required tools are missing.
- `check` is a readiness gate: it only passes when every tool reports `present`, including `openclaw` and `clawteam`.
- `docs/bootstrap-host-runtime.md` explains the `present` / `missing` / `manual` states and the operator decisions to make before install.

---

## Step 2. Decide how OpenClaw and ClawTeam will be installed on this host

This repo intentionally does **not** hardcode one universal installer for `openclaw` and `clawteam`.

When you want the bootstrap script to install them, export:

```bash
export OPENCLAW_INSTALL_CMD='<your host-specific openclaw install command>'
export CLAWTEAM_INSTALL_CMD='<your host-specific clawteam install command>'
```

Example shape only:

```bash
export OPENCLAW_INSTALL_CMD='npm install -g openclaw'
export CLAWTEAM_INSTALL_CMD='pip install clawteam'
```

Use the real commands that match your environment.

Also note:
- `uv` may be hinted rather than installed automatically depending on package manager availability
- `gh` may also require host-specific install flow depending on OS

---

## Step 3. Dry-run the host installation

```bash
scripts/bootstrap-host-runtime.sh install --dry-run --runtime-root /srv/clawhost
```

This is the safest first execution because it:
- shows what would happen
- creates no destructive side effects
- confirms your chosen runtime root
- shows the exact install commands or hints the bootstrap will use for each missing tool

Recommended runtime root:

```text
/srv/clawhost
```

You can change it if needed.

---

## Step 4. Run the host installation for real

```bash
scripts/bootstrap-host-runtime.sh install --runtime-root /srv/clawhost
```

This creates the base host layout:
- runtime root
- bin/
- instances/
- logs/
- cache/

The script will:
- install tools it knows how to install safely
- execute `OPENCLAW_INSTALL_CMD` / `CLAWTEAM_INSTALL_CMD` if you provided them
- warn for tools that still need manual installation

Optional Linux/systemd starting point:
- `examples/services/systemd/clawhost-instance.env.example`
- `examples/services/systemd/clawhost-instance-bootstrap@.service`

These assets do **not** create a full poller/gateway daemon stack; they give you a concrete host-local wrapper for bootstrap + instance create/start so you do not have to invent the first service wiring from scratch.

---

# Project instance setup

Once the host runtime is prepared, create a project instance.

## Step 5. Create an instance from a repo URL

Example for your target repo:

```bash
python3 scripts/clawhost-instance.py create \
  --instances-root /srv/clawhost/instances \
  --name llm-report-module \
  --repo-url https://github.com/sejeonglee/llm-report-module
```

This materializes:
- `config/project-instance.json`
- `state/runtime.json`
- `state/github-issue-cursor.json`
- manual brief intake directories
- worktree root
- logs dir

The instance is configured for:
- `github_issue_polling`
- `manual_brief`

and uses conservative defaults for:
- `max_parallel_tasks`
- `max_active_worktrees`

Those are configuration defaults, not hardcoded 8GB assumptions.

---

## Step 6. Start the instance

```bash
python3 scripts/clawhost-instance.py start \
  --instances-root /srv/clawhost/instances \
  --name llm-report-module
```

This marks the instance `running` and ensures the polling/runtime state is materialized.

---

## Step 7. Inspect instance status

```bash
python3 scripts/clawhost-instance.py status \
  --instances-root /srv/clawhost/instances \
  --name llm-report-module
```

This shows:
- repo slug
- repo URL
- polling interval
- worktree root
- cursor path
- runtime task/worktree caps
- manual brief inbox path

---

# Config boundary model

This package assumes 3 layers.

## 1. Host-global
Applies to the whole host.

Examples:
- runtime root
- instances root
- logs root
- host-wide concurrency caps
- memory policy
- secret env var references
- shared OpenClaw control plane settings

Example file:
- `examples/config/host-global.json`

## 2. Project-instance
Applies to one repo-backed instance.

Examples:
- repo URL
- repo slug
- poll interval
- state root
- worktrees root
- intake sources

Example file:
- `examples/config/project-instance.json`

## 3. Per-task ephemeral
Applies only to a single executing task.

Examples:
- task id
- branch name
- worktree path
- PR number
- retry lease
- temporary runtime files

Example file:
- `examples/config/task-ephemeral.json`

Validate both boundaries and runtime isolation with:

```bash
python3 tools/config_boundary.py \
  examples/config/host-global.json \
  examples/config/project-instance.json \
  examples/config/task-ephemeral.json

python3 tools/runtime_isolation.py \
  examples/config/host-global.json \
  examples/config/project-instance.json \
  examples/config/task-ephemeral.json
```

---

# Host sizing and scaling

This package does **not** hardcode one host size.

It uses configurable host-global knobs such as:
- `max_active_instances`
- `max_parallel_tasks`
- `host_memory_gb`
- `reserved_memory_gb`
- `max_memory_per_instance_gb`
- `max_memory_per_task_gb`
- `scale_profile`

So you can start conservatively and later move from a smaller host to a 24GB host by **changing config**, not rewriting the package.

See:
- `examples/config/host-global.json`
- `docs/config-boundary.md`
- `docs/runtime-isolation.md`

---

# Docker harness: isolated full-package test

If you want to test the package in a completely isolated container, use the Docker harness.

## Dry-run the harness first

```bash
scripts/run-docker-harness.sh \
  --dry-run \
  --repo-url https://github.com/sejeonglee/llm-report-module \
  --artifacts-dir .artifacts/docker-harness
```

This prints the exact `docker build` and `docker run` commands.

## Run the harness for real

```bash
scripts/run-docker-harness.sh \
  --repo-url https://github.com/sejeonglee/llm-report-module \
  --artifacts-dir .artifacts/docker-harness
```

Important properties:
- the repo URL is passed at runtime via `docker run`
- the repo is **not** baked into the image
- artifacts are written back to the host via a mounted artifacts directory

Expected Docker harness outputs include:
- generated project-instance and task-ephemeral artifacts
- validator logs proving generated artifacts match the canonical schema
- `bootstrap-plan.json`
- `bootstrap-install.log`
- `instance-create.json`
- `instance-start.json`
- `instance-status.json`
- `summary.json`

See:
- `docs/docker-harness.md`

---

# One-command full verification

To validate the package end-to-end on the current host:

```bash
scripts/run-verification.sh \
  --repo-url https://github.com/sejeonglee/llm-report-module \
  --artifacts-dir .artifacts/verification
```

This runs:
1. Python unit tests
2. Python compile checks
3. Bash syntax checks
4. Generated project-instance artifact validation
5. Docker harness dry-run
6. Docker harness live execution

Expected top-level artifact:
- `.artifacts/verification/summary.json`

If you just want the command plan:

```bash
scripts/run-verification.sh \
  --dry-run \
  --repo-url https://github.com/sejeonglee/llm-report-module \
  --artifacts-dir .artifacts/verification
```

---

# Minimal “I want to start now” checklist

If you want the shortest path:

```bash
# 1. clone
cd /where/you/want
 git clone <THIS-REPO-URL> clawhost-kit
cd clawhost-kit

# 2. inspect host requirements
scripts/bootstrap-host-runtime.sh plan --json

# 3. set real install commands for host-specific tools
export OPENCLAW_INSTALL_CMD='<your real openclaw install command>'
export CLAWTEAM_INSTALL_CMD='<your real clawteam install command>'

# 4. dry-run install
scripts/bootstrap-host-runtime.sh install --dry-run --runtime-root /srv/clawhost

# 5. real install
scripts/bootstrap-host-runtime.sh install --runtime-root /srv/clawhost

# 6. create instance
python3 scripts/clawhost-instance.py create \
  --instances-root /srv/clawhost/instances \
  --name llm-report-module \
  --repo-url https://github.com/sejeonglee/llm-report-module

# 7. start instance
python3 scripts/clawhost-instance.py start \
  --instances-root /srv/clawhost/instances \
  --name llm-report-module

# 8. inspect instance
python3 scripts/clawhost-instance.py status \
  --instances-root /srv/clawhost/instances \
  --name llm-report-module
```

If you want to validate everything first without trusting the host:

```bash
scripts/run-verification.sh \
  --repo-url https://github.com/sejeonglee/llm-report-module \
  --artifacts-dir .artifacts/verification
```

---

# What is still operator-defined?

These are intentionally **not** fully automated in a one-size-fits-all way:
- exact `openclaw` install command
- exact `clawteam` install command
- real GitHub authentication model
- real polling daemon service wiring
- real OpenClaw gateway service wiring

This repo gives you:
- the package structure
- the boundary model
- the instance lifecycle
- the Docker isolation harness
- the verification path

So yes — **you can start setting this up right now on the current host** — but for a real production-like install you still need to choose the exact OpenClaw/ClawTeam installation commands for your OS and environment.

If you want the shortest clarification on what the repo does vs. what you still need to decide, read:
- `docs/bootstrap-host-runtime.md`

---

# Supporting docs

- `docs/bootstrap-host-runtime.md`
- `docs/project-instance-lifecycle.md`
- `docs/config-boundary.md`
- `docs/runtime-isolation.md`
- `docs/docker-harness.md`
- `docs/verification.md`
- `examples/services/systemd/`
