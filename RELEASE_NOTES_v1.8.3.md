# Python 3.15 Data Engineering Validation Lab v1.8.3

## Summary

v1.8.3 packages the hardened release workflow and current Python 3.15 readiness validation state.

## Highlights

- Hardened `scripts/release.sh` to build version-matched archives from Git HEAD.
- Prevented exploded release folders from being left under `releases/`.
- Added safer release workflow options:
  - `--dry-run`
  - `--skip-tests`
  - `--allow-dirty`
- Confirmed local validation and release checksum generation.
- Packaged release archive and checksum for v1.8.3.

## Validation

- Full compatibility validation completed successfully.
- Repository validation tests passing.
- Release checksum verified.

## Release Artifacts

- `releases/python315-dataeng-validation-v1.8.3.zip`
- `releases/python315-dataeng-validation-v1.8.3.zip.sha256`

## Tag

- `v1.8.3`
