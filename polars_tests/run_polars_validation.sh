#!/usr/bin/env bash
# =============================================================================
# Project : Python 3.15 Data Engineering Validation Suite
# Author  : Dr. Ceasar Jackson Jr.
# File    : polars_tests/run_polars_validation.sh
#
# Purpose
#   Run the full Polars per-library validation suite against Python 3.15.
#   Executes each test script and the benchmark in sequence, stops at the
#   first failure, and reports PASS/FAIL for every step.
#
# Usage
#   From any directory (the script moves to the repository root itself):
#     bash polars_tests/run_polars_validation.sh
#     DRY_RUN=1 bash polars_tests/run_polars_validation.sh   # print, do not run
#     PYTHON=/path/to/python bash polars_tests/run_polars_validation.sh
#   Interpreter order: $PYTHON, then <repo>/.venv/bin/python, then python.
#   Set NO_COLOR=1 to disable color; color is off automatically when piped.
#
# Validation
#   Runs: test_polars_version, test_polars_dataframe, test_polars_groupby, test_polars_join, benchmark_polars
#
# Exit Codes
#   0   every step passed (or DRY_RUN=1 listed them)
#   1   a prerequisite is missing or a step failed
#   2   invalid command-line usage
#   130 interrupted (Ctrl-C)
#
# Log files
#   logs/polars_validation_<YYYYmmdd_HHMMSS>.log (plain text), flat in logs/ to match
#   the repo logger and the logs/*.log .gitignore rule.
#   Best-effort: a read-only filesystem downgrades to console-only output.
# =============================================================================

# -E so the ERR trap fires inside functions; -u catches typos; pipefail so the
# `| tee` used for the log file cannot hide a failing step. Without these a
# failed step could still end in "VALIDATION PASSED".
set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
SUITE="polars_validation"
DRY_RUN="${DRY_RUN:-0}"

# --- logging ----------------------------------------------------------------
# Color only on a real terminal and when NO_COLOR is unset; the file sink is
# always plain text so logs stay greppable.
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  C_RESET=$'\033[0m'; C_CYAN=$'\033[36m'; C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'; C_RED=$'\033[31m'
else
  C_RESET=""; C_CYAN=""; C_GREEN=""; C_YELLOW=""; C_RED=""
fi

LOG_FILE=""
init_log() {
  local dir="${PROJECT_ROOT}/logs"
  local file
  file="${dir}/${SUITE}_$(date +%Y%m%d_%H%M%S).log"
  # Best-effort: never let an unwritable logs/ directory abort validation.
  if mkdir -p -- "${dir}" 2>/dev/null && : >"${file}" 2>/dev/null; then
    LOG_FILE="${file}"
  fi
}

# log LEVEL COLOR message...
log() {
  local level="$1" color="$2"; shift 2
  local IFS=' '  # "$*"/"${a[*]}" join with IFS's first char; the global IFS starts with a newline
  printf '%s[%-4s]%s %s\n' "${color}" "${level}" "${C_RESET}" "$*"
  if [[ -n "${LOG_FILE}" ]]; then
    printf '[%-4s] %s\n' "${level}" "$*" >>"${LOG_FILE}" 2>/dev/null || true
  fi
}
log_info() { log INFO "${C_CYAN}" "$@"; }
log_pass() { log PASS "${C_GREEN}" "$@"; }
log_warn() { log WARN "${C_YELLOW}" "$@"; }
log_fail() { log FAIL "${C_RED}" "$@" >&2; }

usage() {
  sed -n '/^# Usage/,/^# Validation/p' "${BASH_SOURCE[0]}" | sed '$d; s/^# \{0,1\}//'
}

# 130 = 128 + SIGINT, the shell convention for "stopped by Ctrl-C".
trap 'printf "\n" >&2; log_warn "Interrupted by user."; exit 130' INT

# --- arguments ----------------------------------------------------------------
case "${1:-}" in
  "") ;;
  -h|--help) usage; exit 0 ;;
  *) printf 'Unknown argument: %s (this runner takes none; use DRY_RUN=1 or PYTHON=...)\n' "$1" >&2
     usage >&2; exit 2 ;;
esac
if [[ "${DRY_RUN}" != "0" && "${DRY_RUN}" != "1" ]]; then
  printf 'DRY_RUN must be 0 or 1. Got %q.\n' "${DRY_RUN}" >&2
  exit 2
fi

# --- prerequisites ------------------------------------------------------------
# Resolve the interpreter once, up front, so a bad PYTHON fails with a fix
# instead of halfway through the suite. The documented PYTHON override wins.
if [[ -n "${PYTHON:-}" ]]; then
  PY="${PYTHON}"
elif [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
  PY="${PROJECT_ROOT}/.venv/bin/python"
else
  PY="python"
fi

STEPS=(
  test_polars_version
  test_polars_dataframe
  test_polars_groupby
  test_polars_join
  benchmark_polars
)

init_log
# Tests use paths relative to the repo root, so run from there.
cd -- "${PROJECT_ROOT}"

if ! command -v -- "${PY}" >/dev/null 2>&1; then
  log_fail "Python interpreter not found: ${PY}. Create .venv or run: PYTHON=/path/to/python bash ${BASH_SOURCE[0]}"
  exit 1
fi
for step in "${STEPS[@]}"; do
  if [[ ! -f "polars_tests/${step}.py" ]]; then
    log_fail "Missing script: polars_tests/${step}.py. Restore it with: git checkout -- polars_tests/${step}.py"
    exit 1
  fi
done

# run_step "Label" script_name -- echoes the command, runs it, tees to the log.
run_step() {
  local label="$1" script="$2"
  local IFS=' '  # "$*"/"${a[*]}" join with IFS's first char; the global IFS starts with a newline
  local cmd=("${PY}" "polars_tests/${script}.py")
  # `|| return 1` is deliberate: bash disables set -e inside a function that
  # is called from `if !`, so without it a failing step would fall through to
  # the PASS line below and the suite could report success after a failure.
  printf '+ %s\n' "${cmd[*]}"
  if [[ "${DRY_RUN}" == "1" ]]; then
    log_info "DRY_RUN: would run ${script}.py"
    return 0
  fi
  if [[ -n "${LOG_FILE}" ]]; then
    printf '+ %s\n' "${cmd[*]}" >>"${LOG_FILE}" 2>/dev/null || true
    "${cmd[@]}" 2>&1 | tee -a "${LOG_FILE}" || return 1
  else
    "${cmd[@]}" || return 1
  fi
  log_pass "${label} validation complete"
}

printf '\n============================================================\n'
printf 'POLARS VALIDATION SUITE\n'
printf 'Python %s\n' "$("${PY}" --version 2>&1 | cut -d' ' -f2)"
[[ -n "${LOG_FILE}" ]] && printf 'Log: %s\n' "${LOG_FILE}"
printf '============================================================\n\n'

FAILED=0
for entry in "${STEPS[@]}"; do
  case "${entry}" in
    test_polars_version) label="Version" ;;
    test_polars_dataframe) label="DataFrame" ;;
    test_polars_groupby) label="Group-by" ;;
    test_polars_join) label="Join" ;;
    benchmark_polars) label="Benchmark" ;;
  esac
  # An `if` guards the call so set -e does not abort before we can name the
  # failing step in the log.
  if ! run_step "${label}" "${entry}"; then
    log_fail "${label} validation FAILED (polars_tests/${entry}.py)"
    FAILED=1
    break
  fi
  printf '\n'
done

if [[ "${FAILED}" -ne 0 ]]; then
  log_fail "POLARS VALIDATION FAILED"
  exit 1
fi
if [[ "${DRY_RUN}" == "1" ]]; then
  log_info "POLARS DRY RUN COMPLETE (nothing was executed)"
  exit 0
fi
log_pass "POLARS VALIDATION PASSED"
