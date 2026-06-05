import polars as pl

print("=" * 60)
print("POLARS VALIDATION")
print("=" * 60)

print("Polars Version:", pl.__version__)

df = pl.DataFrame({"id":[1,2,3]})

print("DataFrame Creation: PASS")
print(df)
