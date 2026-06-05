import polars as pl

df = pl.DataFrame({
    "name": ["Alice","Bob","Charlie"],
    "salary": [100000,125000,95000]
})

result = df.sort("salary", descending=True)

print("DATAFRAME TEST")
print(result)
