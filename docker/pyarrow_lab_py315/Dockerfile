# =============================================================================
# Project : Python 3.15 Data Engineering Validation Suite
# Author  : Dr. Ceasar Jackson Jr.
# File    : docker/pyarrow_lab_py315/Dockerfile
#
# Purpose
# -------
# Linux arm64 image on the SAME Python as the host validation (3.15.1), so the
# report generator's Docker PySpark/PyArrow probe tests 3.15.1 and not the
# 3.14.x runtime inside the older pyarrow-dataeng:py314 image.
#
# Why a new directory
# -------------------
# docker/pyarrow_lab and docker_pyarrow_lab build the historical py314 image
# that earlier reports cite. They are left untouched so that evidence stays
# reproducible.
#
# Build (from the repo root; needs network, roughly 1 GB)
# -------------------------------------------------------
#   docker build -t pyarrow-dataeng:py315 docker/pyarrow_lab_py315
#
# Use
# ---
#   python scripts/generate_report.py --release 3.15.1 --docker-image pyarrow-dataeng:py315
#   DATAENG_DOCKER_IMAGE=pyarrow-dataeng:py315 python scripts/validate_extended.py
#
# Compatibility decisions
# -----------------------
# * Compiled packages are installed with --only-binary=:all:, so a missing
#   cp315 wheel fails the build loudly. It must never fall back to a silent,
#   slow source build (that is how a "tested on 3.15" claim goes wrong).
#   Verified 2026-10-26 on PyPI for manylinux aarch64: pyarrow 26.0.0, pandas
#   3.1.0 and numpy 2.5.4 have native cp315 wheels, duckdb has an abi3 wheel,
#   polars is a pure-Python wheel.
# * PySpark is published only as a source distribution (pure Python), so it is
#   installed separately without --only-binary.
# * JAVA_HOME is resolved at build time instead of hardcoding the arm64 path.
# =============================================================================
FROM python:3.15.1-slim

LABEL maintainer="Dr. Ceasar Jackson Jr."
LABEL description="Python 3.15.1 + OpenJDK 21 + PyArrow + PySpark (validation probe image)"
LABEL project="python315_test"

RUN apt-get update && apt-get install -y --no-install-recommends \
        procps openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Stable JAVA_HOME regardless of CPU architecture.
RUN ln -s "$(dirname "$(dirname "$(readlink -f "$(which java)")")")" /opt/java
ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"
RUN java -version

# Driver and worker must be the same interpreter, or the first Python UDF fails
# with a version-mismatch error.
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
ENV PYSPARK_SUBMIT_ARGS="--conf spark.ui.enabled=false pyspark-shell"

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --only-binary=:all: \
        pyarrow duckdb pandas polars numpy
RUN pip install --no-cache-dir pyspark

WORKDIR /workspace
COPY smoke_test.py /workspace/smoke_test.py

# Build-time check: fails the build unless the container runs 3.15 and a Python
# UDF executes on a worker with the same interpreter.
RUN python3 /workspace/smoke_test.py
