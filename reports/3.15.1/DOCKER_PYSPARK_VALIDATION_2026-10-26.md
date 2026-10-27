# Python 3.15.1 — Supplemental Docker PySpark Validation

Author: Dr. Ceasar Jackson Jr.
Recorded UTC: 2026-10-27T02:14:40.035477+00:00

## Environment

- Docker image: pyarrow-dataeng:py315
- Image ID: sha256:f0a7f39f5577949dbb8d380c0e7a82866d48879604231bb1241d7f26da7efcab
- Architecture: arm64
- Container runtime: Python 3.15.1
- Base image: python:3.15.1-slim
- Java: OpenJDK 21
- PySpark: 4.2.0
- PyArrow: 26.0.0

## Validation

Previously completed smoke tests reported PASS for:

- Spark local session initialization
- DataFrame count and aggregation
- Python UDF execution
- Worker and driver Python version agreement
- Extended PySpark validation on Python 3.15.1

The Docker image identity, architecture, and Python runtime
were independently rechecked when this record was created.

## Evidence Provenance

The original compatibility report recorded PySpark as SKIP.
The reconciled manifest and evidence.json record PySpark PASS.
The manifest's py314 image reference is explicitly identified
as carried-over baseline metadata, not reverified evidence.

## Limitations

- Local Spark execution only; cluster mode not tested.
- Arrow/pandas-backed Spark interoperability not tested.
- PySpark warns about incomplete pandas >= 3.0 support.
- Production deployment readiness is not established.

## Release Assessment

15 PASS, 2 BLOCKED, 0 SKIP.
Provisional readiness: 94%; not an official release score.

Historical manifests and compatibility reports were not
modified by creation of this supplemental record.
