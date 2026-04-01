#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ARTIFACTS_DIR="${ARTIFACTS_DIR:-$REPO_ROOT/.artifacts/verification}"
REPO_URL=""
DRY_RUN=0

while (($#)); do
  case "$1" in
    --repo-url)
      shift
      REPO_URL=$1
      ;;
    --artifacts-dir)
      shift
      ARTIFACTS_DIR=$1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
  shift
done

if [[ -z "$REPO_URL" ]]; then
  echo "--repo-url is required" >&2
  exit 1
fi

mkdir -p "$ARTIFACTS_DIR"

STEP_LABELS=(unit-tests python-compile bash-syntax generated-artifact-validation docker-harness-dry-run docker-harness-live)
STEP_COMMANDS=(
  "python3 -m unittest discover -s tests -p 'test_*.py'"
  "python3 -m py_compile scripts/*.py tools/*.py"
  "bash -n scripts/bootstrap-host-runtime.sh && bash -n scripts/run-docker-harness.sh && bash -n scripts/run-verification.sh && bash -n docker/harness-entrypoint.sh"
  "python3 scripts/verify-generated-artifacts.py --repo-url $REPO_URL --artifacts-dir $ARTIFACTS_DIR/generated-artifact-validation"
  "scripts/run-docker-harness.sh --dry-run --repo-url $REPO_URL --artifacts-dir $ARTIFACTS_DIR/docker-harness"
  "scripts/run-docker-harness.sh --repo-url $REPO_URL --artifacts-dir $ARTIFACTS_DIR/docker-harness"
)

if (( DRY_RUN )); then
  python3 - <<'PY' "$REPO_URL" "$ARTIFACTS_DIR" "${STEP_LABELS[@]}" -- "${STEP_COMMANDS[@]}"
import json, sys
repo_url = sys.argv[1]
artifacts_dir = sys.argv[2]
sep = sys.argv.index('--')
labels = sys.argv[3:sep]
commands = sys.argv[sep + 1:]
print(json.dumps({
    'repo_url': repo_url,
    'artifacts_dir': artifacts_dir,
    'steps': [
        {'label': label, 'command': command}
        for label, command in zip(labels, commands)
    ],
}))
PY
  exit 0
fi

run_and_capture() {
  local label=$1
  local command=$2
  local logfile="$ARTIFACTS_DIR/${label}.log"
  echo "==> $label"
  bash -lc "$command" | tee "$logfile"
}

run_and_capture "unit-tests" "${STEP_COMMANDS[0]}"
run_and_capture "python-compile" "${STEP_COMMANDS[1]}"
run_and_capture "bash-syntax" "${STEP_COMMANDS[2]}"
run_and_capture "generated-artifact-validation" "${STEP_COMMANDS[3]}"
run_and_capture "docker-harness-dry-run" "${STEP_COMMANDS[4]}"
run_and_capture "docker-harness-live" "${STEP_COMMANDS[5]}"

python3 - <<PY > "$ARTIFACTS_DIR/summary.json"
import json
from pathlib import Path
artifacts = Path(${ARTIFACTS_DIR@Q})
summary = {
    'repo_url': ${REPO_URL@Q},
    'artifacts_dir': str(artifacts),
    'logs': sorted(p.name for p in artifacts.glob('*.log')),
    'docker_artifacts': sorted(p.name for p in (artifacts / 'docker-harness').glob('*')),
    'generated_artifacts': sorted(p.name for p in (artifacts / 'generated-artifact-validation').glob('*')),
}
print(json.dumps(summary))
PY

cat "$ARTIFACTS_DIR/summary.json"
