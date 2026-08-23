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
# =============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="${PROJECT_ROOT}/releases"
LOG_DIR="${PROJECT_ROOT}/logs"

VERSION=""
ALLOW_DIRTY=0
DRY_RUN=0
SKIP_TESTS=0
PYTHON_BIN="${PYTHON_BIN:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
  printf "%b\n" "$*"
}

info() {
  log "${BLUE}INFO:${NC} $*"
}

ok() {
  log "${GREEN}OK:${NC} $*"
}

warn() {
  log "${YELLOW}WARN:${NC} $*"
}

err() {
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
  if [[ -f "${PROJECT_ROOT}/tools/sync_readiness.py" ]]; then
    info "Synchronizing readiness artifacts"
    run "${PYTHON_BIN}" "${PROJECT_ROOT}/tools/sync_readiness.py"
    ok "Readiness synchronization completed"
  else
    warn "tools/sync_readiness.py not found; skipping readiness synchronization."
  fi
}

build_archive() {
  local archive_name="python315-dataeng-validation-${VERSION}.zip"
  local archive_path="${RELEASE_DIR}/${archive_name}"
  local checksum_path="${archive_path}.sha256"
  local prefix="python315-dataeng-validation-${VERSION}/"

  info "Preparing release directory"
  run mkdir -p "${RELEASE_DIR}"
  run mkdir -p "${LOG_DIR}"

  info "Removing prior same-version archive files"
  run rm -f "${archive_path}" "${checksum_path}"

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

  ok "Archive built: ${archive_path}"
  ok "Checksum built: ${checksum_path}"
}

print_next_steps() {
  local archive_name="python315-dataeng-validation-${VERSION}.zip"
  local notes_file="RELEASE_NOTES_${VERSION}.md"

  log "${GREEN}====================================================${NC}"
  log "${GREEN}Release Build Complete${NC}"
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
  run_validation
  sync_readiness
  build_archive
  print_next_steps
}

main "$@"