# Python 3.15 Validation Releases

## Purpose

This directory contains versioned release archives for the
Python 3.15 Data Engineering Validation Lab.

## Release Artifacts

Release archives and their SHA-256 checksum files are tracked
in Git.

Standard artifact names:

- `python315-dataeng-validation-vX.Y.Z.zip`
- `python315-dataeng-validation-vX.Y.Z.zip.sha256`

Existing historical releases must be preserved.

## Release Integrity

Release archives are generated from committed Git HEAD using
`scripts/release.sh`.

Each archive must have a matching SHA-256 checksum file.

Verify archive integrity before committing, tagging, or
publishing release artifacts.

ZIP files may require explicit staging with `git add -f`
because of repository ignore rules.

## Local Backups

The `releases/_backups/` directory is reserved for local,
ignored backups.

These backups must not be included in release commits.

External backup locations may also be maintained separately.

## Release Process

See `docs/RELEASE_PROCESS.md` for the complete release workflow.

Release documentation must be committed before the archive
is generated.

Release publication requires explicit approval.

## Python 3.15.2 Readiness

The v2.2.1 maintenance release retains a readiness assessment
of **94% PROVISIONAL**.

This assessment must not be represented as full production
readiness.
