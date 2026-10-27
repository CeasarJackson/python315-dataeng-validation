# Python 3.15.1 — Advanced PySpark and Arrow Schema Validation

Author: Dr. Ceasar Jackson Jr.

Validation date: 2026-10-26

Validation time: 22:40 EDT

## Purpose

Evaluate advanced Spark SQL schema behavior and Arrow-enabled
pandas interoperability under Python 3.15.1.

This report supplements existing Python 3.15.1 compatibility
evidence without modifying historical reports or manifests.

## Environment

- Python: 3.15.1
- PySpark: 4.2.0
- PyArrow: 26.0.0
- pandas: 3.1.0
- Java: OpenJDK 21
- Architecture: Linux arm64
- Docker image: pyarrow-dataeng:py315
- Image ID: sha256:f0a7f39f5577949dbb8d380c0e7a82866d48879604231bb1241d7f26da7efcab
- Spark execution mode: local[2]
- Docker memory limit: 4 GB
- Docker CPU limit: 4
- Docker networking: disabled

## Spark Configuration

- spark.sql.session.timeZone=UTC
- spark.sql.execution.arrow.pyspark.enabled=true
- spark.sql.execution.arrow.pyspark.fallback.enabled=false

Container hostname and Spark networking were explicitly
configured for loopback operation.

## Validation Results

| Test | Result |
|---|---|
| Nested StructType | PASS |
| ArrayType with nullable elements | PASS |
| MapType with nullable values | PASS |
| UTC timestamp and null handling | PASS |
| DecimalType(18,4) precision | PASS |
| Arrow-enabled pandas/Spark round-trip with nulls | PASS |

Total: 6 PASS, 0 FAIL.

Process exit code: 0.

## Functional Findings

### Nested structures

Nested fields were successfully created and retrieved.

Null values within nested structures were preserved.

### Arrays

ArrayType supported integer arrays containing null elements.

Empty arrays were preserved.

### Maps

MapType supported nullable values.

Empty maps were preserved.

### Timestamps

UTC timestamp values were successfully represented using
Spark TimestampType.

Null timestamps were preserved.

### Decimal precision

DecimalType(18,4) preserved the tested decimal value
123456.7890 without loss of precision.

Null decimal values were preserved.

### Arrow interoperability

A pandas DataFrame containing string and floating-point
columns was converted to Spark and back to pandas.

Null counts and row counts were preserved.

Arrow was enabled and fallback was disabled.

## Compatibility Warning

PySpark 4.2.0 emitted a FutureWarning indicating that
pandas >= 3.0.0 is not yet fully supported.

The warning did not prevent the tested workloads from passing.

## Scope Limitations

- Spark ran in local mode only.
- Cluster execution was not evaluated.
- Complex Spark schemas were validated using native Spark
  operations, not individual Arrow-backed round-trips.
- Timestamp timezone edge cases were not exhaustively tested.
- Decimal overflow and boundary conditions were not tested.
- Large-scale datasets and performance were not evaluated.
- Production deployment readiness is not established.

## Evidence Provenance

This report supplements:

- DOCKER_PYSPARK_VALIDATION_2026-10-26.md
- ARROW_PANDAS_INTEROPERABILITY_2026-10-26.md
- ARROW_NULLS_PANDAS_UDF_2026-10-26.md

Earlier reports retain their original historical context.

The original compatibility report, manifests and evidence.json
were not modified by this validation.

## Release Assessment

Existing provisional readiness: 94%.

No readiness-score adjustment is claimed.

These results expand functional coverage but do not establish
complete upstream compatibility or production readiness.
