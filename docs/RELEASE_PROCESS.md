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
cd ~/Projects/python315_test
git status --short
python -m pytest -q
bash -n scripts/release.sh
bash scripts/release.sh vX.Y.Z --dry-run --skip-tests
bash scripts/release.sh vX.Y.Z
git add -f releases/python315-dataeng-validation-vX.Y.Z.zip releases/python315-dataeng-validation-vX.Y.Z.zip.sha256
git commit -m "chore: add vX.Y.Z packaged release archive"
git push origin main
git add RELEASE_NOTES_vX.Y.Z.md
git commit -m "docs: add vX.Y.Z release notes"
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
