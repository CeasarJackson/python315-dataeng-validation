# Python 3.15 Data Engineering Validation Lab — v1.8.2 Plan

## Primary Goal

Harden the release workflow after v1.8.1 by improving CI, release repeatability, and future Python 3.15 milestone tracking.

## Candidate Work Items

1. Add GitHub Actions CI
   - Run pytest on push and pull request.
   - Validate manifest schema.
   - Validate readiness consistency.
   - Validate release artifact generation.

2. Add release workflow validation
   - Ensure zip files and sha256 files are generated consistently.
   - Ensure checksum files are verified from the releases directory.
   - Prevent accidental tracking of exploded release folders.

3. Improve release script safety
   - Refuse dirty working trees unless explicitly overridden.
   - Confirm target version argument.
   - Generate release notes stub.
   - Print next-step GitHub CLI commands.

4. Add future Python 3.15 release placeholders
   - 3.15.0rc3 if applicable.
   - 3.15.0ga placeholder.
   - Ensure readiness progression tests continue to pass.

5. Improve documentation
   - Add release process runbook.
   - Add validation checklist.
   - Add artifact policy for zip files vs exploded folders.

## Validation Target

python -m pytest -q
shasum -a 256 -c releases/python315-dataeng-validation-v1.8.1.zip.sha256
git status --short

## Proposed Version

v1.8.2
