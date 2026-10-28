#!/usr/bin/env bash
# =============================================================================
# Script: release.sh
# Author: Dr. Ceasar Jackson Jr.
# Purpose: Build a version-matched Python 3.15 Data Engineering Validation release.
#
# Usage:
#   bash scripts/release.sh <version>
#   bash scripts/release.sh v1.8.3
#   bash scripts/release.sh v1.8.3 --allow-dirty
#   bash scripts/release.sh v2.2.0 --python-release 3.15.2
#
# Validation:
#   bash -n scripts/release.sh
#   bash scripts/release.sh v1.8.3 --dry-run
#   python -m pytest -q
#
# Output:
#   releases/python315-dataeng-validation-<version>.zip
#   releases/python315-dataeng-validation-<version>.zip.sha256
#
# Notes:
#   - This script intentionally builds a zip archive directly from Git HEAD.
#   - It does not leave exploded release folders under releases/.
#   - It refuses to run on a dirty tree unless --allow-dirty is supplied.
#   - --dry-run prints every mutating command instead of running it.
#
# Exit Codes:
#   0    Success (or --help / --dry-run completed).
#   1    Prerequisite, git-state, validation or build failure.
#   2    Invalid command-line usage.
#   130  Interrupted by Ctrl-C (shell convention: 128 + SIGINT).
# =============================================================================

# -E: ERR traps reach functions; -u: typos fail loudly; pipefail: a failing
# stage in `a | tee b` cannot be hidden by tee's success.
# IFS without a space: an unquoted expansion can never word-split a path.
set -Eeuo pipefail
IFS=$'\n\t'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="${PROJECT_ROOT}/releases"
LOG_DIR="${PROJECT_ROOT}/logs"

VERSION=""
ALLOW_DIRTY=0
DRY_RUN=0
SKIP_TESTS=0
PYTHON_BIN="${PYTHON_BIN:-}"
PYTHON_RELEASE=""
EXPECTED_PYTHON_RELEASE=""

# Color only on a real terminal and when NO_COLOR is unset, so piped output and
# log files never contain raw escape sequences.
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi

log() {
  local IFS=' '  # "$*"/"${a[*]}" join with IFS's first char; the global IFS starts with a newline
  printf "%b\n" "$*"
}

info() {
  local IFS=' '  # "$*"/"${a[*]}" join with IFS's first char; the global IFS starts with a newline
  log "${BLUE}INFO:${NC} $*"
}

ok() {
  local IFS=' '  # "$*"/"${a[*]}" join with IFS's first char; the global IFS starts with a newline
  log "${GREEN}OK:${NC} $*"
}

warn() {
  local IFS=' '  # "$*"/"${a[*]}" join with IFS's first char; the global IFS starts with a newline
  log "${YELLOW}WARN:${NC} $*"
}

err() {
  local IFS=' '  # "$*"/"${a[*]}" join with IFS's first char; the global IFS starts with a newline
  log "${RED}ERROR:${NC} $*" >&2
}

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/release.sh <version> [options]

Required:
  <version>              Semantic release version, for example v1.8.3

Options:
  --allow-dirty          Permit release build when git working tree has changes
  --dry-run              Show intended actions without writing archive files
  --skip-tests           Skip validation/test commands
  --python-release X.Y.Z Python release the build must run on (required
                         unless --dry-run); refuses a mismatched interpreter
  -h, --help             Show this help text

Examples:
  bash scripts/release.sh v1.8.3
  bash scripts/release.sh v1.8.3 --dry-run
  bash scripts/release.sh v1.8.3 --allow-dirty

Post-build GitHub release command:
  gh release create <version> \
    releases/python315-dataeng-validation-<version>.zip \
    releases/python315-dataeng-validation-<version>.zip.sha256 \
    --title "Python 3.15 Data Engineering Validation Lab <version>" \
    --notes-file RELEASE_NOTES_<version>.md
USAGE
}

run() {
  local IFS=' '  # "$*"/"${a[*]}" join with IFS's first char; the global IFS starts with a newline
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    info "DRY_RUN: $*"
  else
    "$@"
  fi
}

parse_args() {
  if [[ "$#" -eq 0 ]]; then
    usage
    err "Missing required version argument, for example v1.8.3."
    exit 2
  fi

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      -h|--help)
        usage
        exit 0
        ;;
      --allow-dirty)
        ALLOW_DIRTY=1
        shift
        ;;
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      --skip-tests)
        SKIP_TESTS=1
        shift
        ;;
      --python-release)
        if [[ "$#" -lt 2 ]] || [[ ! "$2" =~ ^3\.15\.[0-9]+$ ]]; then
          err "--python-release needs a value like 3.15.2."
          exit 2
        fi
        EXPECTED_PYTHON_RELEASE="$2"
        shift 2
        ;;
      v[0-9]*.[0-9]*.[0-9]*)
        if [[ -n "${VERSION}" ]]; then
          err "Multiple version arguments provided: ${VERSION} and $1"
          exit 2
        fi
        VERSION="$1"
        shift
        ;;
      *)
        err "Unknown argument: $1"
        usage
        exit 2
        ;;
    esac
  done

  if [[ -z "${VERSION}" ]]; then
    err "Missing required version argument, for example v1.8.3."
    exit 2
  fi

  # A stale .venv (3.15.0) is the silent fallback interpreter; making the
  # target explicit on real builds stops it from stamping the wrong release.
  if [[ "${DRY_RUN}" -eq 0 && -z "${EXPECTED_PYTHON_RELEASE}" ]]; then
    err "Real builds require --python-release X.Y.Z, for example 3.15.2."
    exit 2
  fi
}

require_command() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    err "Required command not found: ${cmd}"
    exit 1
  fi
}

resolve_python_bin() {
  local candidate=""

  if [[ -n "${PYTHON_BIN:-}" ]]; then
    candidate="${PYTHON_BIN}"
  elif [[ -n "${VIRTUAL_ENV:-}" ]] && [[ -x "${VIRTUAL_ENV}/bin/python" ]]; then
    candidate="${VIRTUAL_ENV}/bin/python"
  elif [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    candidate="${PROJECT_ROOT}/.venv/bin/python"
  elif command -v python >/dev/null 2>&1; then
    candidate="$(command -v python)"
  else
    err "Unable to resolve a Python interpreter."
    exit 1
  fi

  if [[ "${candidate}" != /* ]]; then
    if command -v "${candidate}" >/dev/null 2>&1; then
      candidate="$(command -v "${candidate}")"
    elif [[ -x "${PROJECT_ROOT}/${candidate}" ]]; then
      candidate="${PROJECT_ROOT}/${candidate}"
    fi
  fi

  if [[ ! -x "${candidate}" ]]; then
    err "Resolved PYTHON_BIN is not executable: ${candidate}"
    exit 1
  fi

  PYTHON_BIN="${candidate}"
  export PYTHON_BIN

  info "Python interpreter: ${PYTHON_BIN}"
  info "Python runtime: $("${PYTHON_BIN}" --version 2>&1)"

  PYTHON_RELEASE="$("${PYTHON_BIN}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
  [[ "${PYTHON_RELEASE}" =~ ^3\.15\.[0-9]+$ ]] || {
    err "Unsupported Python release: ${PYTHON_RELEASE}"
    exit 1
  }
  info "Python report release: ${PYTHON_RELEASE}"

  if [[ -n "${EXPECTED_PYTHON_RELEASE}" ]]; then
    if [[ "${PYTHON_RELEASE}" != "${EXPECTED_PYTHON_RELEASE}" ]]; then
      err "Interpreter is Python ${PYTHON_RELEASE}, expected ${EXPECTED_PYTHON_RELEASE}."
      err "Set PYTHON_BIN or activate the matching venv, then rerun."
      exit 1
    fi
    ok "Interpreter matches --python-release ${EXPECTED_PYTHON_RELEASE}"
  else
    warn "No --python-release given (dry run); interpreter release is unchecked."
  fi
}


validate_git_state() {
  info "Checking git working tree state"

  if ! git -C "${PROJECT_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    err "Project root is not inside a git repository: ${PROJECT_ROOT}"
    exit 1
  fi

  if [[ "${ALLOW_DIRTY}" -eq 0 ]] && [[ -n "$(git -C "${PROJECT_ROOT}" status --short)" ]]; then
    err "Git working tree is dirty. Commit/stash changes or rerun with --allow-dirty."
    git -C "${PROJECT_ROOT}" status --short >&2
    exit 1
  fi

  ok "Git working tree check passed"
}

run_validation() {
  if [[ "${SKIP_TESTS}" -eq 1 ]]; then
    warn "Skipping validation because --skip-tests was supplied."
    return 0
  fi

  info "Running validation"

  if [[ -x "${PROJECT_ROOT}/scripts/validate_all.sh" ]]; then
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      info "DRY_RUN: PYTHON_BIN=${PYTHON_BIN} bash ${PROJECT_ROOT}/scripts/validate_all.sh"
    else
      PYTHON_BIN="${PYTHON_BIN}" bash "${PROJECT_ROOT}/scripts/validate_all.sh"
    fi
  else
    warn "scripts/validate_all.sh is missing or not executable; running pytest only."
  fi

  run "${PYTHON_BIN}" -m pytest -q
  ok "Validation completed"
}

sync_readiness() {
  local manifest="${PROJECT_ROOT}/reports/${PYTHON_RELEASE}/manifest.json"

  if [[ ! -f "${manifest}" ]]; then
    err "Canonical manifest missing: ${manifest}"
    exit 1
  fi

  if ! "${PYTHON_BIN}" -c '
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
sys.exit(0 if manifest.get("release") == sys.argv[2] else 1)
' "${manifest}" "${PYTHON_RELEASE}"; then
    err "Canonical manifest release does not match ${PYTHON_RELEASE}"
    exit 1
  fi

  if [[ ! -f "${PROJECT_ROOT}/tools/sync_readiness.py" ]]; then
    err "Required readiness synchronizer is missing."
    exit 1
  fi

  info "Synchronizing readiness for Python ${PYTHON_RELEASE}"
  run "${PYTHON_BIN}" "${PROJECT_ROOT}/tools/sync_readiness.py" \
    --release "${PYTHON_RELEASE}"
  ok "Readiness synchronization completed"
}

preflight_release_destinations() {
  # Reject occupied release destinations before running tests or modifying
  # readiness reports. Include dangling symlinks, which -e alone misses.
  local archive_name="python315-dataeng-validation-${VERSION}.zip"
  local archive_path="${RELEASE_DIR}/${archive_name}"
  local checksum_path="${archive_path}.sha256"

  info "Preflight: checking release artifact destinations"

  if [[ -e "${archive_path}" || -L "${archive_path}" ||
        -e "${checksum_path}" || -L "${checksum_path}" ]]; then
    err "Release artifacts already exist; refusing to overwrite."
    err "Archive: ${archive_path}"
    err "Checksum: ${checksum_path}"
    exit 1
  fi

  ok "Release artifact destinations are available"
}

build_archive() {
  local archive_name="python315-dataeng-validation-${VERSION}.zip"
  local archive_path="${RELEASE_DIR}/${archive_name}"
  local checksum_path="${archive_path}.sha256"
  local prefix="python315-dataeng-validation-${VERSION}/"

  info "Preparing release directory"
  run mkdir -p "${RELEASE_DIR}"
  run mkdir -p "${LOG_DIR}"

  if [[ -e "${archive_path}" || -L "${archive_path}" ||
        -e "${checksum_path}" || -L "${checksum_path}" ]]; then
    err "Release artifacts already exist; refusing to overwrite."
    err "Archive: ${archive_path}"
    err "Checksum: ${checksum_path}"
    exit 1
  fi

  info "Building archive from Git HEAD"
  run git -C "${PROJECT_ROOT}" archive \
    --format=zip \
    --output="${archive_path}" \
    --prefix="${prefix}" \
    HEAD

  info "Writing checksum"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    info "DRY_RUN: shasum -a 256 ${archive_name} > ${archive_name}.sha256"
  else
    (
      cd "${RELEASE_DIR}"
      shasum -a 256 "${archive_name}" > "${archive_name}.sha256"
      shasum -a 256 -c "${archive_name}.sha256"
    )
  fi

  if [[ "${DRY_RUN}" -eq 1 ]]; then
    info "DRY_RUN: Archive would be built: ${archive_path}"
    info "DRY_RUN: Checksum would be written: ${checksum_path}"
  else
    ok "Archive built: ${archive_path}"
    ok "Checksum built: ${checksum_path}"
  fi
}

print_next_steps() {
  local archive_name="python315-dataeng-validation-${VERSION}.zip"
  local notes_file="RELEASE_NOTES_${VERSION}.md"

  log "${GREEN}====================================================${NC}"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "${YELLOW}Release Dry Run Complete - no artifacts created${NC}"
  else
    log "${GREEN}Release Build Complete${NC}"
  fi
  log "${GREEN}====================================================${NC}"
  log "Version : ${VERSION}"
  log "Archive : ${RELEASE_DIR}/${archive_name}"
  log "Checksum: ${RELEASE_DIR}/${archive_name}.sha256"
  log ""
  log "Next validation commands:"
  log "  cd ${PROJECT_ROOT}"
  log "  (cd releases && shasum -a 256 -c ${archive_name}.sha256)"
  log "  ${PYTHON_BIN} -m pytest -q"
  log "  git status --short"
  log ""
  log "Suggested git commands:"
  log "  git add -f releases/${archive_name} releases/${archive_name}.sha256"
  log "  git commit -m \"chore: add ${VERSION} packaged release archive\""
  log "  git push origin main"
  log "  git tag -a ${VERSION} -m \"Python 3.15 data engineering validation ${VERSION}\""
  log "  git push origin ${VERSION}"
  log ""
  log "Suggested GitHub release command:"
  log "  gh release create ${VERSION} \\"
  log "    releases/${archive_name} \\"
  log "    releases/${archive_name}.sha256 \\"
  log "    --title \"Python 3.15 Data Engineering Validation Lab ${VERSION}\" \\"
  log "    --notes-file ${notes_file}"
}

main() {
  parse_args "$@"

  log "${YELLOW}====================================================${NC}"
  log "${YELLOW}Python 3.15 Release Builder${NC}"
  log "${YELLOW}====================================================${NC}"
  log "Version: ${VERSION}"
  log "Project: ${PROJECT_ROOT}"
  log "Dry run: ${DRY_RUN}"

  require_command git
  resolve_python_bin
  require_command shasum

  validate_git_state
  preflight_release_destinations
  run_validation
  sync_readiness
  build_archive
  print_next_steps
}

main "$@"