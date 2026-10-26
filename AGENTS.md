# Codex Development Instructions

## Project

Repository: python315_test

Purpose:
Validate Python 3.15 compatibility, dependency readiness,
release engineering, and associated testing infrastructure.

## 1. General Operating Principles

- Preserve all existing work.
- Inspect before modifying.
- Prefer minimal, targeted changes.
- Never overwrite unrelated changes.
- Distinguish verified facts from assumptions.
- Report failures explicitly.
- Do not claim a fix succeeded without verification.

## 2. Repository Safety

Before modifying files:

1. Confirm the repository root.
2. Inspect Git status.
3. Identify existing modifications.
4. Preserve unrelated work.
5. Create timestamped backups when appropriate.
6. Explain the intended changes.

Never execute destructive Git operations without explicit approval.

Prohibited without authorization:

- git reset --hard
- git clean -fd
- git push --force
- git rebase
- git commit
- git push

Do not stage files without approval.

## 3. Python Environment

Use the repository virtual environment:

.venv/bin/python

Do not assume that python or python3 on PATH refers to
the repository interpreter.

Never install, upgrade, or remove dependencies without approval.

Prefer:

.venv/bin/python -m pip

Avoid indiscriminate dependency upgrades.

## 4. Code Quality

For Python changes, use the repository's configured tools.

When available:

- Black
- pytest
- Ruff
- Project-specific validation scripts

Do not introduce new tools or dependencies without approval.

## 5. Testing and Validation

Before reporting completion:

1. Run relevant syntax checks.
2. Run applicable formatting checks.
3. Run relevant tests.
4. Run git diff --check.
5. Inspect git diff.
6. Verify actual on-disk changes.
7. Report test results and failures.

Do not run destructive or externally mutating tests without approval.

## 6. Backups

Create timestamped backups before significant changes.

Preserve file permissions where practical.

Never overwrite existing backup files.

Avoid placing temporary backups inside tracked source directories.

## 7. Logging

For substantial operations:

- Include timestamps.
- Report executed commands.
- Preserve useful diagnostic output.
- Use persistent logs when appropriate.
- Never log credentials or secrets.

## 8. Git Workflow

Before changes:

git status --short --branch

After changes:

git diff --check
git diff --stat
git status --short --branch

Do not automatically stage, commit, tag, or push.

Require explicit authorization for those actions.

## 9. Security

- Never expose credentials or tokens.
- Do not inspect secret files unless necessary and authorized.
- Do not transmit private repository content to external services
  beyond the explicitly authorized Codex workflow.
- Do not modify security settings without approval.

## 10. Communication

Provide concise, evidence-based summaries.

For every modification, report:

- Files changed
- Reason for change
- Backup location, if applicable
- Validation commands
- Validation results
- Remaining issues

Wait for approval before performing destructive operations,
dependency changes, commits, pushes, or external deployments.
