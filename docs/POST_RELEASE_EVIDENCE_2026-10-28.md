# Python 3.15.2 post-release evidence checkpoint — 2026-10-28

Status: **94% PROVISIONAL — not an official release score**. This additive checkpoint does not replace or regenerate existing reports, manifests, PDFs or v2.2.1 artifacts.

## Provenance and results

Source conversation: Continue Project Testing, ID `6ae145e5-557c-83ea-8470-ba32eb0ccfd9`. The retrieved attachment `Pasted text.txt` includes a failed Docker-daemon attempt at 02:16:10 EDT and a successful attempt beginning **2026-10-28 02:16:32 EDT**. The [saved excerpt](evidence/targeted_pyspark_arrow_2026-10-28.txt) preserves the successful run output verbatim, excluding unrelated terminal history and the shell prompt. It is supplied historical evidence, not a fresh execution.

Excerpt SHA256: `1aaa9a3d93445cb5b7160d0c552b38d3d7809d5909552bc87e17ebf2a03a8b6c`.

| Evidence | Result | Verification level |
|---|---|---|
| Advanced interoperability | 5/5 PASS | Reported in the source conversation; original transcript unavailable |
| Targeted nullable/Arrow/pandas UDF checks | 8/8 PASS | Confirmed in supplied terminal transcript |
| Full pytest suite | 331 passed, one skipped | Fresh Python 3.15.2 rerun: 331 passed, one skipped in 3.35s |
| Readiness | 94% PROVISIONAL | Existing manifest and reconciled Markdown reports |
| MLflow / Ray | BLOCKED / BLOCKED | Existing resolution evidence; no fresh package-index check |

The combined 13/13 claim comprises five conversation-reported advanced checks and eight transcript-confirmed targeted checks. These are not 13 additional pytest test cases.

## Targeted checks

1. Arrow enabled, fallback disabled.
2. Nullable pandas input.
3. pandas to Spark with explicit schema.
4. Nullable integer/string preservation.
5. pandas UDF result `[20, 40, None, 80]`.
6. Spark to pandas nullable round-trip.
7. Spark schema preservation.
8. Four workers reporting Python 3.15.2.

Runtime: Python 3.15.2 / PySpark 4.2.0 / PyArrow 26.0.0 / pandas 3.1.0; Linux ARM64; Docker image `pyarrow-dataeng:py3152`, ID `sha256:399f6f34c8bd2c2b6b19b13eef1af0e98f7354499f06957bffb7556e3d877666`. Scope is local mode (`local[2]`), not cluster validation or universal compatibility. PySpark warned that pandas >=3.0 is not fully supported. Other warnings include the incubator vector module, native Hadoop library fallback and generated hardware address.

## Release and evidence integrity

Read-only review verified local HEAD, origin/main and peeled v2.2.1 at `a9623d759f9923808470d7b1a039ec40a96be676`. No fetch or independent hosted-asset verification was performed. Local v2.2.1 ZIP SHA256 matches its sidecar: `ebe4aee3aad28d317a08d82693f29e62b7e3d4a40b7824f7e4483b6ffc30f7c5`.

Existing baseline manifest SHA256: `b7e4668ed29cec839640243d69e34f88756b6e154f1f65832aa55f6feee6889a`.
Existing evidence.json SHA256: `04bae52bb4b1c411b0c1cdc5d167afb4e9c6b61f6adbfdf9367c2b3db7b25c7f`.

The targeted transcript also confirms 30 compatible host packages and preservation of the original four documentation modifications at that time. Those are historical run results, not a fresh environment check.

## Review correction and follow-up

The initial review incorrectly identified missing EXPECTED_PYTHON forwarding as a Docker test defect. `docker/pyarrow_lab_py315/Dockerfile` sets `ENV EXPECTED_PYTHON=${PYTHON_VERSION}`, inherited by containers. No test fix is warranted for this finding.

`STATUS.md` retains older summaries. This checkpoint is the current documentation pointer; historical report files remain intact. Obtain the original advanced-run output before upgrading its provenance. No commit, staging, push, tagging, dependency changes or release regeneration is included.

Read-only integrity commands, from the repository root:

```sh
git rev-parse HEAD origin/main 'v2.2.1^{}'
git diff --check
git diff --stat
git diff --cached --stat
shasum -a 256 docs/evidence/targeted_pyspark_arrow_2026-10-28.txt
shasum -a 256 reports/3.15.2/manifest.baseline.json reports/3.15.2/evidence.json
(cd releases && shasum -a 256 -c python315-dataeng-validation-v2.2.1.zip.sha256)
```

## Checkpoint verification — 2026-10-28

Command: `.venv3152/bin/python -m pytest -q -p no:cacheprovider`. Result: **331 passed, one skipped in 3.35s**. The skipped test is opt-in Docker integration; Docker interoperability was not rerun. The initial sandboxed attempt returned 328 passed, three failed, one skipped because repository log writes were denied; the authorized rerun passed without code changes.

All nine local Markdown links checked resolve. `git diff --check` passed. HEAD, local origin/main and peeled v2.2.1 remain at the recorded commit; release ZIP, baseline manifest and evidence.json hashes still match the values above. No staged changes, commits, pushes or regenerated artifacts.
