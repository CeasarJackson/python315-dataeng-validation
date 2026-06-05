import polars as pl

employees = pl.DataFrame({
    "id":[1,2,3],
    "name":["Alice","Bob","Charlie"]
})

departments = pl.DataFrame({
    "id":[1,2,3],
    "dept":["IT","Finance","HR"]
})

result = employees.join(
    departments,
    on="id",
    how="inner"
)

print("JOIN TEST")
print(result)
