# Python 3.15.1 — Arrow/pandas Interoperability Validation

Author: Dr. Ceasar Jackson Jr.
Recorded UTC: 2026-10-27T02:16:19.874511+00:00

## Environment

- Python: 3.15.1
- PySpark: 4.2.0
- PyArrow: 26.0.0
- pandas: 3.1.0
- Docker image: pyarrow-dataeng:py315
- Architecture: Linux arm64

## Validation

A functional interoperability smoke test was executed
on 2026-10-26 at approximately 22:15 EDT.

The test:

1. Created a pandas DataFrame containing integer and float data.
2. Converted the pandas DataFrame to a Spark DataFrame.
3. Converted the Spark DataFrame back to pandas.
4. Verified the resulting values using assertions.
5. Ran with Arrow enabled and Arrow fallback disabled.

## Results

- PASS: pandas to Spark conversion.
- PASS: Spark to pandas conversion.
- PASS: Round-trip data integrity.
- PASS: Arrow enabled with fallback disabled.
- PASS: Process exit code 0.

## Compatibility Warning

PySpark 4.2.0 emitted a FutureWarning indicating that
pandas >= 3.0.0 is not yet fully supported.

The warning did not prevent this workload from passing.

## Limitations

- Only a small DataFrame was tested.
- Cluster-mode execution was not tested.
- Complex schemas and null handling were not tested.
- pandas UDF compatibility was not tested.
- Full upstream compatibility is not established.
- Production deployment readiness is not established.

## Evidence Provenance

This validation occurred after creation of:

DOCKER_PYSPARK_VALIDATION_2026-10-26.md

The earlier document remains historically accurate
for its original recording time.

The original compatibility report, manifests, and
evidence.json were not modified by this validation.

## Release Assessment

Existing provisional readiness: 94%.

No readiness-score adjustment is claimed.
