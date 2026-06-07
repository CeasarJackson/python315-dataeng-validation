# Python 3.15 Data Engineering Validation Lab v1.8.2

## Summary

This patch release finalizes the CI-stable validation workflow after the v1.8.1 release package.

## Changes

- Added GitHub Actions validation workflow for the Python 3.15 preview lab.
- Fixed CI dependency installation by using `uv pip`.
- Limited CI pytest scope to repository validation tests under `tests/`.
- Made pytest validation scope explicit in `pytest.ini`.
- Opted into Node 24 execution for GitHub Actions.
- Confirmed release archive checksum validation in CI.

## Validation

- Local validation: `47 passed`
- GitHub Actions: passing
- Release checksum verification: passing

## Release Artifacts

- `releases/python315-dataeng-validation-v1.8.1.zip`
- `releases/python315-dataeng-validation-v1.8.1.zip.sha256`

## Tag

- `v1.8.2`
