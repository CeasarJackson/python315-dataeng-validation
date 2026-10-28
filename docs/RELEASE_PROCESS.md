# Python 3.15 Data Engineering Validation Lab Release Process

## Purpose

This runbook defines the standard release workflow for the Python 3.15 Data Engineering Validation Lab.

## Release Rules

1. Release archives must be version-matched.
2. Release archives must be built from Git HEAD using scripts/release.sh.
3. Exploded release folders should not be tracked.
4. The release tag should point to the final release commit.
5. GitHub release assets must match the release version.

## Standard Release Flow

Replace vX.Y.Z with the target version.

```bash
cd ~/Projects/python315_test || return 1

PYTHON_BIN="$PWD/.venv3152/bin/python"

"$PYTHON_BIN" --version || return 1
"$PYTHON_BIN" -m pytest -q || return 1
uv pip check --python "$PYTHON_BIN" || return 1
bash -n scripts/release.sh || return 1

# Commit documentation before building the archive.
git add RELEASE_NOTES_vX.Y.Z.md docs/RELEASE_PROCESS.md releases/README.md
git diff --cached --check || return 1
git commit -m "docs: prepare vX.Y.Z release documentation" || return 1

# The builder requires a clean working tree.
[[ -z "$(git status --porcelain)" ]] || return 1

# Dry run without creating artifacts.
PYTHON_BIN="$PYTHON_BIN" bash scripts/release.sh \
    vX.Y.Z --python-release 3.15.2 --dry-run || return 1

# Build once, from committed Git HEAD.
PYTHON_BIN="$PYTHON_BIN" bash scripts/release.sh \
    vX.Y.Z --python-release 3.15.2 || return 1

# Verify archive integrity before staging.
(cd releases && shasum -a 256 -c \
    python315-dataeng-validation-vX.Y.Z.zip.sha256) || return 1
git add -f releases/python315-dataeng-validation-vX.Y.Z.zip releases/python315-dataeng-validation-vX.Y.Z.zip.sha256
git commit -m "chore: add vX.Y.Z packaged release archive"
git push origin main
git tag -a vX.Y.Z -m "Python 3.15 data engineering validation vX.Y.Z"
git push origin vX.Y.Z
gh release create vX.Y.Z releases/python315-dataeng-validation-vX.Y.Z.zip releases/python315-dataeng-validation-vX.Y.Z.zip.sha256 --title "Python 3.15 Data Engineering Validation Lab vX.Y.Z" --notes-file RELEASE_NOTES_vX.Y.Z.md
```

## Final Validation

```bash
gh release view vX.Y.Z --json tagName,name,isDraft,isPrerelease,url,assets --jq '{tagName,name,isDraft,isPrerelease,url,assets:[.assets[].name]}'
(cd releases && shasum -a 256 -c python315-dataeng-validation-vX.Y.Z.zip.sha256)
python -m pytest -q
git status --short
git log --oneline --decorate -8
```
