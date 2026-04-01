#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DOCKERFILE="$REPO_ROOT/docker/harness.Dockerfile"
IMAGE_TAG="${IMAGE_TAG:-clawhost-harness:local}"
REPO_URL=""
ARTIFACTS_DIR="${ARTIFACTS_DIR:-$REPO_ROOT/.artifacts/docker-harness}"
INSTANCE_NAME="${INSTANCE_NAME:-harness-instance}"
DRY_RUN=0
SKIP_BUILD=0

json_escape() {
  python3 - <<'PY' "$1"
import json, sys
print(json.dumps(sys.argv[1]))
PY
}

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
    --instance-name)
      shift
      INSTANCE_NAME=$1
      ;;
    --image-tag)
      shift
      IMAGE_TAG=$1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    --skip-build)
      SKIP_BUILD=1
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
BUILD_COMMAND=(docker build -f "$DOCKERFILE" -t "$IMAGE_TAG" "$REPO_ROOT")
RUN_COMMAND=(docker run --rm -e "REPO_URL=$REPO_URL" -e "INSTANCE_NAME=$INSTANCE_NAME" -e "ARTIFACTS_DIR=/artifacts" -v "$ARTIFACTS_DIR:/artifacts" "$IMAGE_TAG")

if (( DRY_RUN )); then
  python3 - <<'PY' "$REPO_URL" "$DOCKERFILE" "$ARTIFACTS_DIR" "$IMAGE_TAG" "$INSTANCE_NAME" "${BUILD_COMMAND[*]}" "${RUN_COMMAND[*]}"
import json, sys
print(json.dumps({
  "repo_url": sys.argv[1],
  "dockerfile": sys.argv[2],
  "artifacts_dir": sys.argv[3],
  "image_tag": sys.argv[4],
  "instance_name": sys.argv[5],
  "build_command": sys.argv[6].split(),
  "run_command": sys.argv[7].split(),
}))
PY
  exit 0
fi

command -v docker >/dev/null 2>&1 || { echo "docker not found" >&2; exit 1; }

if (( ! SKIP_BUILD )); then
  "${BUILD_COMMAND[@]}"
fi
"${RUN_COMMAND[@]}"
