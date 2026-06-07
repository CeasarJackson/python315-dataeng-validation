#!/usr/bin/env bash
# =============================================================================
# Script: release.sh
# Author: Dr. Ceasar Jackson Jr.
# Purpose: Build a complete Python 3.15 Data Engineering Validation release.
#
# Usage:
#   bash scripts/release.sh
#
# Validation:
#   bash -n scripts/release.sh
#
# Output:
#   releases/python315-dataeng-validation-<version>.zip
# =============================================================================

set -euo pipefail

VERSION="${1:-v1.8.0}"
STAMP="$(date +%Y%m%d_%H%M%S)"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_DIR="${PROJECT_ROOT}/releases"
BUILD_DIR="${RELEASE_DIR}/python315-dataeng-validation-${VERSION}"
LOG_DIR="${PROJECT_ROOT}/logs"

mkdir -p "${RELEASE_DIR}"
mkdir -p "${LOG_DIR}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "$1"
}

log "${YELLOW}====================================================${NC}"
log "${YELLOW}Python 3.15 Release Builder${NC}"
log "${YELLOW}====================================================${NC}"

log "${BLUE}Step 1: Validation${NC}"
bash "${PROJECT_ROOT}/scripts/validate_all.sh"

log "${BLUE}Step 2: Report Generation${NC}"

if [[ -f "${PROJECT_ROOT}/scripts/generate_report.py" ]]; then
    python "${PROJECT_ROOT}/scripts/generate_report.py" --release "${VERSION}"
fi

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

log "${BLUE}Step 3: Package Project${NC}"

cp -R \
    README.md \
    ROADMAP.md \
    STATUS.md \
    PROJECT_STRUCTURE.md \
    PORTFOLIO_SUMMARY.md \
    reports \
    docs \
    scripts \
    sqlite_tests \
    sqlalchemy_tests \
    duckdb_tests \
    polars_tests \
    airflow_tests \
    notebooks \
    "${BUILD_DIR}/"

log "${BLUE}Step 4: Create Manifest${NC}"

cat > "${BUILD_DIR}/manifest.json" <<EOF
{
  "version": "${VERSION}",
  "timestamp": "${STAMP}",
  "python_version": "$(python --version 2>&1)",
  "status": "validated"
}
EOF

log "${BLUE}Step 5: Build Archive${NC}"

cd "${RELEASE_DIR}"

ZIP_FILE="python315-dataeng-validation-${VERSION}.zip"

rm -f "${ZIP_FILE}"

zip -rq "${ZIP_FILE}" "$(basename "${BUILD_DIR}")"

shasum -a 256 "${ZIP_FILE}" > "${ZIP_FILE}.sha256"

log "${GREEN}====================================================${NC}"
log "${GREEN}Release Complete${NC}"
log "${GREEN}====================================================${NC}"
log "Archive : ${RELEASE_DIR}/${ZIP_FILE}"
log "Checksum: ${RELEASE_DIR}/${ZIP_FILE}.sha256"