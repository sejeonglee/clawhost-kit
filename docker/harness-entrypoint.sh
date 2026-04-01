#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${REPO_URL:?REPO_URL is required}
ARTIFACTS_DIR=${ARTIFACTS_DIR:-/artifacts}
INSTANCE_NAME=${INSTANCE_NAME:-harness-instance}
INSTANCES_ROOT=${INSTANCES_ROOT:-/tmp/clawhost-harness/instances}
RUNTIME_ROOT=${RUNTIME_ROOT:-/tmp/clawhost-harness/runtime}
OPENCLAW_INSTALL_CMD=${OPENCLAW_INSTALL_CMD:-"echo install-openclaw-placeholder"}
CLAWTEAM_INSTALL_CMD=${CLAWTEAM_INSTALL_CMD:-"echo install-clawteam-placeholder"}

mkdir -p "$ARTIFACTS_DIR"

CLAWHOST_PRESENT_TOOLS="git,tmux,python3" \
CLAWHOST_MISSING_TOOLS="node,uv,gh,openclaw,clawteam" \
OPENCLAW_INSTALL_CMD="$OPENCLAW_INSTALL_CMD" \
CLAWTEAM_INSTALL_CMD="$CLAWTEAM_INSTALL_CMD" \
/workspace/scripts/bootstrap-host-runtime.sh plan --json --package-manager apt-get \
  > "$ARTIFACTS_DIR/bootstrap-plan.json"

CLAWHOST_PRESENT_TOOLS="git,tmux,python3" \
CLAWHOST_MISSING_TOOLS="node,uv,gh,openclaw,clawteam" \
OPENCLAW_INSTALL_CMD="$OPENCLAW_INSTALL_CMD" \
CLAWTEAM_INSTALL_CMD="$CLAWTEAM_INSTALL_CMD" \
/workspace/scripts/bootstrap-host-runtime.sh install --dry-run --runtime-root "$RUNTIME_ROOT" \
  > "$ARTIFACTS_DIR/bootstrap-install.log"

python3 /workspace/scripts/clawhost-instance.py create \
  --instances-root "$INSTANCES_ROOT" \
  --name "$INSTANCE_NAME" \
  --repo-url "$REPO_URL" \
  > "$ARTIFACTS_DIR/instance-create.json"

python3 /workspace/scripts/clawhost-instance.py start \
  --instances-root "$INSTANCES_ROOT" \
  --name "$INSTANCE_NAME" \
  > "$ARTIFACTS_DIR/instance-start.json"

python3 /workspace/scripts/clawhost-instance.py status \
  --instances-root "$INSTANCES_ROOT" \
  --name "$INSTANCE_NAME" \
  > "$ARTIFACTS_DIR/instance-status.json"

python3 - <<PY > "$ARTIFACTS_DIR/summary.json"
import json
from pathlib import Path
artifacts = Path("${ARTIFACTS_DIR}")
instance_create = json.loads((artifacts / "instance-create.json").read_text())
summary = {
    "repo_url": instance_create["repo_slug"],
    "bootstrap_plan_path": str(artifacts / "bootstrap-plan.json"),
    "bootstrap_install_log_path": str(artifacts / "bootstrap-install.log"),
    "instance_create_path": str(artifacts / "instance-create.json"),
    "instance_start_path": str(artifacts / "instance-start.json"),
    "instance_status_path": str(artifacts / "instance-status.json"),
}
print(json.dumps(summary))
PY

cat "$ARTIFACTS_DIR/summary.json"
