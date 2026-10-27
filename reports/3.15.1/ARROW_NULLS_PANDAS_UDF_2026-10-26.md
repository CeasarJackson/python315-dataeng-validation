# Python 3.15.1 — Arrow Null Handling and pandas UDF Validation

Author: Dr. Ceasar Jackson Jr.
Run time: 2026-10-26 approx. 22:39 EDT (02:39 UTC 2026-10-27)

## Environment

- Docker image: pyarrow-dataeng:py315 (image ID sha256:f0a7f39f5577949dbb8d380c0e7a82866d48879604231bb1241d7f26da7efcab)
- Python 3.15.1, pandas 3.1.0, PyArrow 26.0.0, PySpark 4.2.0, OpenJDK 21
- Architecture: Linux arm64
- Run flags: --network none --hostname localhost --add-host localhost:127.0.0.1
  -e SPARK_LOCAL_IP=127.0.0.1 -e SPARK_LOCAL_HOSTNAME=localhost
  --memory 4g --cpus 4
- Spark: local[2], spark.sql.execution.arrow.pyspark.enabled=true,
  spark.sql.execution.arrow.pyspark.fallback.enabled=false

## Results

- PASS: null round-trip (pandas -> Spark -> pandas) with an explicit nullable
  schema (string and double columns, one null each); null counts and non-null
  values preserved.
- PASS: vectorised pandas UDF (double) on the worker; the null stayed null and
  the non-null values were computed correctly (2.5 and 4.5).
- Exit code 0. The test ran with no network access.

## Failed first attempt (test-environment error, not a finding)

An earlier run with --network none and no hostname settings failed with
JAVA_GATEWAY_EXITED. Cause: with no network the container could not resolve its
own hostname (socket.gethostbyname raised gaierror), and Spark resolves the
local host while starting. Setting --hostname localhost, an --add-host entry and
SPARK_LOCAL_IP fixed it. This says nothing about Python 3.15.1 or PySpark.
Reproduce any no-network Spark run with those flags.

## Compatibility Warning

PySpark 4.2.0 still emits FutureWarning: it does not yet fully support
pandas >= 3.0.0. It did not prevent these workloads from passing.

## Limitations

- Three rows; one string and one double column.
- Timestamp, array, map and struct columns not tested.
- Only a scalar vectorised pandas UDF was tested (no grouped-map or Arrow UDFs).
- Local mode only; cluster mode not tested.
- Full upstream compatibility and production readiness are not established.

## Evidence Provenance

This record follows DOCKER_PYSPARK_VALIDATION_2026-10-26.md and
ARROW_PANDAS_INTEROPERABILITY_2026-10-26.md and closes two of the limitations
listed in the latter (null handling, pandas UDF compatibility). Those earlier
documents are unchanged. evidence.json and the manifests were not modified.

## Release Assessment

Existing provisional readiness: 94%. No readiness-score adjustment is claimed.
