#!/usr/bin/env bash
# =============================================================================
# Script: validate_all.sh
# Author: Dr. Ceasar Jackson Jr.
# Purpose: Execute all Python 3.15 Data Engineering validation suites and
#          capture consolidated results in a single log file.
#
# Usage:
#   bash scripts/validate_all.sh
#
# Validation:
#   bash -n scripts/validate_all.sh
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
    echo -e "$1" | tee -a "${LOG_FILE}"
}

run_suite() {
    local suite="$1"

    log "${BLUE}====================================================${NC}"
    log "${BLUE}Running:${NC} ${suite}"
    log "${BLUE}====================================================${NC}"

    if python -m pytest "${suite}" -v 2>&1 | tee -a "${LOG_FILE}"; then
        log "${GREEN}PASS:${NC} ${suite}"
    else
        log "${RED}FAIL:${NC} ${suite}"
        return 1
    fi
}

: > "${LOG_FILE}"

log "${YELLOW}Starting full validation run...${NC}"
log "Project Root: ${PROJECT_ROOT}"
log "Log File: ${LOG_FILE}"

run_suite sqlite_tests
run_suite sqlalchemy_tests
run_suite duckdb_tests
run_suite polars_tests
run_suite airflow_tests

log "${GREEN}All validation suites completed successfully.${NC}"