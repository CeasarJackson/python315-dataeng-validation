import time

import polars as pl

start = time.time()

df = pl.DataFrame({"id": range(100000), "value": [i * 0.5 for i in range(100000)]})

result = df.select(
    [
        pl.col("value").mean().alias("avg_value"),
        pl.col("value").min().alias("min_value"),
        pl.col("value").max().alias("max_value"),
    ]
)

elapsed = time.time() - start

print("POLARS BENCHMARK")
print(result)
print("Elapsed:", round(elapsed, 3), "seconds")
