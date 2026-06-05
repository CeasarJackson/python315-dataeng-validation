import duckdb
import pandas as pd

df = pd.DataFrame({
    "department": ["IT","IT","HR","HR","Finance"],
    "salary": [100000,120000,75000,80000,90000]
})

result = duckdb.sql("""
SELECT
    department,
    AVG(salary) AS avg_salary
FROM df
GROUP BY department
ORDER BY avg_salary DESC
""").df()

print(result)
