import polars as pl

df = pl.DataFrame({
    "department":["IT","IT","HR","HR","Finance"],
    "salary":[100000,120000,75000,80000,90000]
})

result = (
    df.group_by("department")
      .agg(pl.col("salary").mean().alias("avg_salary"))
      .sort("avg_salary", descending=True)
)

print("GROUP BY TEST")
print(result)
