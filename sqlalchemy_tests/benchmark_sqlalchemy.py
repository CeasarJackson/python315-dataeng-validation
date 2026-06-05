from sqlalchemy import create_engine
from sqlalchemy import text
import time

engine = create_engine("sqlite:///:memory:")

start = time.time()

with engine.begin() as conn:

    conn.execute(text("""
        CREATE TABLE numbers(
            id INTEGER,
            value REAL
        )
    """))

    rows = [
        {"id": i, "value": i * 0.5}
        for i in range(100000)
    ]

    conn.execute(
        text("""
            INSERT INTO numbers(id,value)
            VALUES(:id,:value)
        """),
        rows
    )

with engine.connect() as conn:

    result = conn.execute(text("""
        SELECT
            AVG(value),
            MIN(value),
            MAX(value)
        FROM numbers
    """)).fetchone()

elapsed = time.time() - start

print("SQLALCHEMY BENCHMARK")
print(result)
print("Elapsed:", round(elapsed,3), "seconds")
