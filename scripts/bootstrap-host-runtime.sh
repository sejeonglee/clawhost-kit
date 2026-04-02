#!/usr/bin/env bash
set -euo pipefail

ACTION="plan"
OUTPUT_JSON=0
DRY_RUN=0
RUNTIME_ROOT="${CLAWHOST_RUNTIME_ROOT:-/opt/clawhost}"
PACKAGE_MANAGER="${CLAWHOST_PACKAGE_MANAGER:-}"

TOOLS=(git tmux node python3 uv gh openclaw clawteam)
RUNTIME_DIRS=(bin instances logs cache env services)

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap-host-runtime.sh <plan|check|install> [options]

Options:
  --json                     Emit a JSON report for plan/check
  --dry-run                  Print actions instead of executing them
  --runtime-root <path>      Host runtime root (default: /opt/clawhost)
  --package-manager <name>   Override detected package manager (apt-get|brew|manual)
  -h, --help                 Show this help

Environment overrides:
  CLAWHOST_PRESENT_TOOLS     Comma-separated tool ids forced present
  CLAWHOST_MISSING_TOOLS     Comma-separated tool ids forced missing
  OPENCLAW_INSTALL_CMD       Shell command to install openclaw when missing
  CLAWTEAM_INSTALL_CMD       Shell command to install clawteam when missing
EOF
}

json_escape() {
  local value=${1-}
  value=${value//\\/\\\\}
  value=${value//"/\\"}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  printf '%s' "$value"
}

csv_has() {
  local csv=${1-}
  local needle=${2-}
  [[ ",${csv}," == *",${needle},"* ]]
}

detect_package_manager() {
  if [[ -n "$PACKAGE_MANAGER" ]]; then
    printf '%s' "$PACKAGE_MANAGER"
    return
  fi

  if command -v brew >/dev/null 2>&1; then
    printf 'brew'
  elif command -v apt-get >/dev/null 2>&1; then
    printf 'apt-get'
  else
    printf 'manual'
  fi
}

tool_command() {
  case "$1" in
    git) printf 'git' ;;
    tmux) printf 'tmux' ;;
    node) printf 'node' ;;
    python3) printf 'python3' ;;
    uv) printf 'uv' ;;
    gh) printf 'gh' ;;
    openclaw) printf 'openclaw' ;;
    clawteam) printf 'clawteam' ;;
    *) return 1 ;;
  esac
}

tool_present() {
  local tool=$1
  if csv_has "${CLAWHOST_MISSING_TOOLS:-}" "$tool"; then
    return 1
  fi
  if csv_has "${CLAWHOST_PRESENT_TOOLS:-}" "$tool"; then
    return 0
  fi
  command -v "$(tool_command "$tool")" >/dev/null 2>&1
}

step_status() {
  local tool=$1
  if tool_present "$tool"; then
    printf 'present'
    return
  fi

  case "$tool" in
    openclaw)
      if [[ -n "${OPENCLAW_INSTALL_CMD:-}" ]]; then
        printf 'missing'
      else
        printf 'manual'
      fi
      ;;
    clawteam)
      if [[ -n "${CLAWTEAM_INSTALL_CMD:-}" ]]; then
        printf 'missing'
      else
        printf 'manual'
      fi
      ;;
    *)
      printf 'missing'
      ;;
  esac
}

install_array_json() {
  local first=1
  printf '['
  local arg
  for arg in "$@"; do
    if (( first )); then
      first=0
    else
      printf ','
    fi
    printf '"%s"' "$(json_escape "$arg")"
  done
  printf ']'
}

step_install_json() {
  local tool=$1
  local pm=$2
  case "$tool:$pm" in
    git:apt-get) install_array_json sudo apt-get install -y git ;;
    tmux:apt-get) install_array_json sudo apt-get install -y tmux ;;
    node:apt-get) install_array_json sudo apt-get install -y nodejs npm ;;
    python3:apt-get) install_array_json sudo apt-get install -y python3 python3-venv python3-pip ;;
    git:brew) install_array_json brew install git ;;
    tmux:brew) install_array_json brew install tmux ;;
    node:brew) install_array_json brew install node ;;
    python3:brew) install_array_json brew install python ;;
    uv:brew) install_array_json brew install uv ;;
    gh:brew) install_array_json brew install gh ;;
    *) printf '[]' ;;
  esac
}

step_install_hint() {
  local tool=$1
  local pm=$2
  case "$tool:$pm" in
    uv:apt-get)
      printf '%s' 'Run: curl -LsSf https://astral.sh/uv/install.sh | sh'
      ;;
    uv:manual)
      printf '%s' 'Install uv manually: https://docs.astral.sh/uv/getting-started/installation/'
      ;;
    gh:apt-get)
      printf '%s' 'Install GitHub CLI from https://cli.github.com/packages before re-running bootstrap.'
      ;;
    gh:manual)
      printf '%s' 'Install GitHub CLI manually: https://cli.github.com/manual/installation'
      ;;
    openclaw:*)
      printf '%s' 'Set OPENCLAW_INSTALL_CMD to a host-specific installer command for openclaw.'
      ;;
    clawteam:*)
      printf '%s' 'Set CLAWTEAM_INSTALL_CMD to a host-specific installer command for clawteam.'
      ;;
    *)
      printf ''
      ;;
  esac
}

print_step_line() {
  local tool=$1
  local pm=$2
  local status
  status=$(step_status "$tool")
  printf '%-10s %s' "$tool" "$status"
  if [[ "$status" == "missing" ]]; then
    local install_json
    install_json=$(step_install_json "$tool" "$pm")
    if [[ "$install_json" != "[]" ]]; then
      printf ' -> %s' "$install_json"
    else
      printf ' -> %s' "$(step_install_hint "$tool" "$pm")"
    fi
  elif [[ "$status" == "manual" ]]; then
    printf ' -> %s' "$(step_install_hint "$tool" "$pm")"
  fi
  printf '\n'
}

emit_json_report() {
  local pm=$1
  local ready=true
  local missing=()
  local step_payloads=()
  local tool status install_json hint step_json

  for tool in "${TOOLS[@]}"; do
    status=$(step_status "$tool")
    install_json=$(step_install_json "$tool" "$pm")
    hint=$(step_install_hint "$tool" "$pm")

    step_json="{\"id\":\"$(json_escape "$tool")\",\"status\":\"$(json_escape "$status")\""
    if [[ "$install_json" != '[]' ]]; then
      step_json+=",\"install\":${install_json}"
    fi
    if [[ -n "$hint" ]]; then
      step_json+=",\"install_hint\":\"$(json_escape "$hint")\""
    fi
    step_json+="}"
    step_payloads+=("$step_json")

    if [[ "$status" != 'present' ]]; then
      ready=false
      missing+=("$tool")
    fi
  done

  printf '{"runtime_root":"%s","package_manager":"%s","steps":[' \
    "$(json_escape "$RUNTIME_ROOT")" "$(json_escape "$pm")"
  local idx
  for idx in "${!step_payloads[@]}"; do
    if (( idx > 0 )); then
      printf ','
    fi
    printf '%s' "${step_payloads[$idx]}"
  done
  printf '],"summary":{"ready":%s,"missing":[' "$ready"
  for idx in "${!missing[@]}"; do
    if (( idx > 0 )); then
      printf ','
    fi
    printf '"%s"' "$(json_escape "${missing[$idx]}")"
  done
  printf ']}}\n'
}

emit_install_json_report() {
  local pm=$1
  local step_payloads=()
  local tool status install_json hint command_json step_json
  local created_dirs=()
  local dir_name idx

  for dir_name in "${RUNTIME_DIRS[@]}"; do
    created_dirs+=("$RUNTIME_ROOT/$dir_name")
  done

  for tool in "${TOOLS[@]}"; do
    status=$(step_status "$tool")
    install_json=$(step_install_json "$tool" "$pm")
    hint=$(step_install_hint "$tool" "$pm")
    command_json=

    case "$tool" in
      openclaw)
        if [[ -n "${OPENCLAW_INSTALL_CMD:-}" ]]; then
          command_json="\"command\":\"$(json_escape "$OPENCLAW_INSTALL_CMD")\""
        fi
        ;;
      clawteam)
        if [[ -n "${CLAWTEAM_INSTALL_CMD:-}" ]]; then
          command_json="\"command\":\"$(json_escape "$CLAWTEAM_INSTALL_CMD")\""
        fi
        ;;
    esac

    step_json="{\"id\":\"$(json_escape "$tool")\",\"status\":\"$(json_escape "$status")\""
    if [[ "$install_json" != '[]' ]]; then
      step_json+=",\"install\":${install_json}"
    fi
    if [[ -n "$hint" ]]; then
      step_json+=",\"install_hint\":\"$(json_escape "$hint")\""
    fi
    if [[ -n "$command_json" ]]; then
      step_json+=",$command_json"
    fi
    step_json+="}"
    step_payloads+=("$step_json")
  done

  printf '{"runtime_root":"%s","package_manager":"%s","dry_run":%s,"created_directories":[' \
    "$(json_escape "$RUNTIME_ROOT")" "$(json_escape "$pm")" "$([[ "$DRY_RUN" -eq 1 ]] && printf true || printf false)"
  for idx in "${!created_dirs[@]}"; do
    if (( idx > 0 )); then
      printf ','
    fi
    printf '"%s"' "$(json_escape "${created_dirs[$idx]}")"
  done
  printf '],"tool_actions":['
  for idx in "${!step_payloads[@]}"; do
    if (( idx > 0 )); then
      printf ','
    fi
    printf '%s' "${step_payloads[$idx]}"
  done
  printf ']}\n'
}

run_command() {
  if (( DRY_RUN )); then
    if (( ! OUTPUT_JSON )); then
      printf 'DRY RUN %s\n' "$*"
    fi
  else
    if (( OUTPUT_JSON )); then
      "$@" >/dev/null
    else
      "$@"
    fi
  fi
}

run_shell_command() {
  local command=$1
  if (( DRY_RUN )); then
    if (( ! OUTPUT_JSON )); then
      printf 'DRY RUN %s\n' "$command"
    fi
  else
    if (( OUTPUT_JSON )); then
      bash -lc "$command" >/dev/null
    else
      bash -lc "$command"
    fi
  fi
}

install_tool() {
  local tool=$1
  local pm=$2
  local status
  status=$(step_status "$tool")
  if [[ "$status" == 'present' ]]; then
    return 0
  fi

  case "$tool" in
    openclaw)
      if [[ -n "${OPENCLAW_INSTALL_CMD:-}" ]]; then
        run_shell_command "$OPENCLAW_INSTALL_CMD"
      else
        printf 'WARN openclaw install skipped: %s\n' "$(step_install_hint "$tool" "$pm")" >&2
      fi
      return 0
      ;;
    clawteam)
      if [[ -n "${CLAWTEAM_INSTALL_CMD:-}" ]]; then
        run_shell_command "$CLAWTEAM_INSTALL_CMD"
      else
        printf 'WARN clawteam install skipped: %s\n' "$(step_install_hint "$tool" "$pm")" >&2
      fi
      return 0
      ;;
  esac

  case "$tool:$pm" in
    git:apt-get) run_command sudo apt-get install -y git ;;
    tmux:apt-get) run_command sudo apt-get install -y tmux ;;
    node:apt-get) run_command sudo apt-get install -y nodejs npm ;;
    python3:apt-get) run_command sudo apt-get install -y python3 python3-venv python3-pip ;;
    git:brew) run_command brew install git ;;
    tmux:brew) run_command brew install tmux ;;
    node:brew) run_command brew install node ;;
    python3:brew) run_command brew install python ;;
    uv:brew) run_command brew install uv ;;
    gh:brew) run_command brew install gh ;;
    *)
      local hint
      hint=$(step_install_hint "$tool" "$pm")
      if [[ -n "$hint" ]]; then
        printf 'WARN %s install skipped: %s\n' "$tool" "$hint" >&2
      fi
      ;;
  esac
}

while (($#)); do
  case "$1" in
    plan|check|install)
      ACTION=$1
      ;;
    --json)
      OUTPUT_JSON=1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    --runtime-root)
      shift
      RUNTIME_ROOT=$1
      ;;
    --package-manager)
      shift
      PACKAGE_MANAGER=$1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

PM=$(detect_package_manager)
case "$ACTION" in
  plan)
    if (( OUTPUT_JSON )); then
      emit_json_report "$PM"
    else
      for tool in "${TOOLS[@]}"; do
        print_step_line "$tool" "$PM"
      done
    fi
    ;;
  check)
    if (( OUTPUT_JSON )); then
      emit_json_report "$PM"
    else
      for tool in "${TOOLS[@]}"; do
        print_step_line "$tool" "$PM"
      done
    fi
    for tool in "${TOOLS[@]}"; do
      [[ "$(step_status "$tool")" == 'present' ]] || exit 1
    done
    ;;
  install)
    run_command mkdir -p "$RUNTIME_ROOT"
    for dir_name in "${RUNTIME_DIRS[@]}"; do
      run_command mkdir -p "$RUNTIME_ROOT/$dir_name"
    done
    for tool in "${TOOLS[@]}"; do
      install_tool "$tool" "$PM"
    done
    if (( OUTPUT_JSON )); then
      emit_install_json_report "$PM"
    fi
    ;;
  *)
    usage >&2
    exit 1
    ;;
esac
