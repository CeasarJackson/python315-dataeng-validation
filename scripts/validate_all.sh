#!/usr/bin/env bash
# =============================================================================
# Script: validate_all.sh
# Author: Dr. Ceasar Jackson Jr.
# Project: Python 3.15 Data Engineering Validation Suite
# Path: scripts/validate_all.sh
#
# Purpose:
#   Execute all Python 3.15 Data Engineering validation suites using one
#   explicitly resolved Python interpreter and capture consolidated results
#   in a single log file.
#
# Interpreter resolution:
#   1. Explicit PYTHON_BIN environment variable.
#   2. Active VIRTUAL_ENV/bin/python.
#   3. Repository-local .venv/bin/python.
#   4. python found on PATH.
#   5. Fail if no usable interpreter can be resolved.
#
# Usage:
#   bash scripts/validate_all.sh
#   PYTHON_BIN=.venv/bin/python bash scripts/validate_all.sh
#   PYTHON_BIN=/path/to/python3.15 bash scripts/validate_all.sh
#
# Validation:
#   bash -n scripts/validate_all.sh
#   PYTHON_BIN=.venv/bin/python bash scripts/validate_all.sh
#
# Output:
#   logs/validate_all.log
# =============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/validate_all.log"

mkdir -p "${LOG_DIR}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    printf "%b\n" "$1" | tee -a "${LOG_FILE}"
}

fail() {
    log "${RED}ERROR:${NC} $*"
    exit 1
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
        fail "Unable to resolve a Python interpreter."
    fi

    if [[ "${candidate}" != /* ]]; then
        if command -v "${candidate}" >/dev/null 2>&1; then
            candidate="$(command -v "${candidate}")"
        elif [[ -x "${PROJECT_ROOT}/${candidate}" ]]; then
            candidate="${PROJECT_ROOT}/${candidate}"
        fi
    fi

    if [[ ! -x "${candidate}" ]]; then
        fail "Resolved PYTHON_BIN is not executable: ${candidate}"
    fi

    PYTHON_BIN="${candidate}"
    export PYTHON_BIN
}

validate_python_runtime() {
    local version
    local executable

    version="$("${PYTHON_BIN}" --version 2>&1)" || \
        fail "Unable to execute Python interpreter: ${PYTHON_BIN}"

    executable="$("${PYTHON_BIN}" -c 'import sys; print(sys.executable)' 2>/dev/null)" || \
        fail "Unable to inspect Python interpreter: ${PYTHON_BIN}"

    log "${BLUE}Python Bin:${NC} ${PYTHON_BIN}"
    log "${BLUE}Python Runtime:${NC} ${version}"
    log "${BLUE}Python Executable:${NC} ${executable}"
}

run_suite() {
    local suite="$1"

    log "${BLUE}====================================================${NC}"
    log "${BLUE}Running:${NC} ${suite}"
    log "${BLUE}====================================================${NC}"

    if "${PYTHON_BIN}" -m pytest "${suite}" -v 2>&1 | tee -a "${LOG_FILE}"; then
        log "${GREEN}PASS:${NC} ${suite}"
    else
        log "${RED}FAIL:${NC} ${suite}"
        return 1
    fi
}

run_optional_suite() {
    local suite="$1"
    local import_name="$2"

    log "${BLUE}====================================================${NC}"
    log "${BLUE}Optional Suite:${NC} ${suite}"
    log "${BLUE}====================================================${NC}"

    if ! "${PYTHON_BIN}" -c "import ${import_name}" >/dev/null 2>&1; then
        log "${YELLOW}SKIP:${NC} ${suite} (${import_name} is not installed in ${PYTHON_BIN})"
        return 0
    fi

    if "${PYTHON_BIN}" -m pytest "${suite}" -v 2>&1 | tee -a "${LOG_FILE}"; then
        log "${GREEN}PASS:${NC} ${suite}"
    else
        log "${RED}FAIL:${NC} ${suite}"
        return 1
    fi
}

: > "${LOG_FILE}"

resolve_python_bin

log "${YELLOW}Starting full validation run...${NC}"
log "Project Root: ${PROJECT_ROOT}"
log "Log File: ${LOG_FILE}"

validate_python_runtime

run_suite sqlite_tests
run_suite sqlalchemy_tests
run_suite duckdb_tests
run_suite polars_tests

# Apache Airflow is intentionally optional in preview Python environments.
# If installed, its test suite must pass. If unavailable, record a SKIP,
# consistent with the compatibility manifest rather than treating absence
# as a repository-test failure.
run_optional_suite airflow_tests airflow

log "${GREEN}All validation suites completed successfully.${NC}"
