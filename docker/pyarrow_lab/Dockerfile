FROM python:3.14-slim

LABEL maintainer="Dr. Ceasar Jackson Jr."
LABEL description="Python 3.14 + JDK 17 + PyArrow + PySpark"
LABEL project="python315_test - Phase 5, 6 & 7"

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl git procps openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-arm64
ENV PATH="${JAVA_HOME}/bin:${PATH}"
RUN java -version

ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
ENV PYSPARK_SUBMIT_ARGS="--conf spark.ui.enabled=false pyspark-shell"

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
    pyarrow duckdb pyspark pandas polars numpy \
    matplotlib plotly jupyterlab notebook ipykernel ipywidgets tqdm

WORKDIR /workspace
RUN mkdir -p /benchmark_data /tmp/spark-events /tmp/spark-warehouse
ENV SPARK_LOCAL_DIRS=/tmp/spark-local

RUN python3 -c "\
from pyspark.sql import SparkSession;\
spark=SparkSession.builder.master('local[1]').appName('smoke')\
.config('spark.ui.enabled','false').config('spark.driver.memory','768m')\
.getOrCreate();\
spark.sparkContext.setLogLevel('ERROR');\
assert spark.createDataFrame([(1,'ok')],['id','s']).count()==1;\
spark.stop();print('PySpark smoke test PASSED')"

EXPOSE 8888
CMD ["jupyter","lab","--ip=0.0.0.0","--port=8888","--no-browser","--allow-root","--NotebookApp.token=","--NotebookApp.password="]
