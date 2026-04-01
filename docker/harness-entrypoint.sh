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

cp "$INSTANCES_ROOT/$INSTANCE_NAME/config/project-instance.json" \
  "$ARTIFACTS_DIR/generated-project-instance.json"

python3 - <<'PY' "$ARTIFACTS_DIR/generated-project-instance.json" "$ARTIFACTS_DIR/generated-task-ephemeral.json"
import json
import sys
from pathlib import Path

sys.path.insert(0, "/workspace")
from tools.runtime_isolation import build_task_fixture

project = json.loads(Path(sys.argv[1]).read_text())
task = build_task_fixture(project, task_id="sandbox-smoke")
Path(sys.argv[2]).write_text(json.dumps(task, indent=2) + "\n")
PY

python3 /workspace/tools/config_boundary.py \
  /workspace/examples/config/host-global.json \
  "$ARTIFACTS_DIR/generated-project-instance.json" \
  "$ARTIFACTS_DIR/generated-task-ephemeral.json" \
  > "$ARTIFACTS_DIR/generated-config-validation.log"

python3 /workspace/tools/runtime_isolation.py \
  /workspace/examples/config/host-global.json \
  "$ARTIFACTS_DIR/generated-project-instance.json" \
  "$ARTIFACTS_DIR/generated-task-ephemeral.json" \
  > "$ARTIFACTS_DIR/generated-runtime-validation.log"

python3 - <<PY > "$ARTIFACTS_DIR/summary.json"
import json
from pathlib import Path
artifacts = Path("${ARTIFACTS_DIR}")
instance_create = json.loads((artifacts / "instance-create.json").read_text())
summary = {
    "repo_url": instance_create["repo_url"],
    "repo_slug": instance_create["repo_slug"],
    "bootstrap_plan_path": str(artifacts / "bootstrap-plan.json"),
    "bootstrap_install_log_path": str(artifacts / "bootstrap-install.log"),
    "instance_create_path": str(artifacts / "instance-create.json"),
    "instance_start_path": str(artifacts / "instance-start.json"),
    "instance_status_path": str(artifacts / "instance-status.json"),
    "generated_project_instance_path": str(artifacts / "generated-project-instance.json"),
    "generated_task_ephemeral_path": str(artifacts / "generated-task-ephemeral.json"),
    "generated_config_validation_path": str(artifacts / "generated-config-validation.log"),
    "generated_runtime_validation_path": str(artifacts / "generated-runtime-validation.log"),
}
print(json.dumps(summary))
PY

cat "$ARTIFACTS_DIR/summary.json"
