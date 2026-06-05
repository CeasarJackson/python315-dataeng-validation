from sqlalchemy import create_engine
from sqlalchemy import text

engine = create_engine("sqlite:///:memory:")

with engine.connect() as conn:

    conn.execute(text("""
        CREATE TABLE employees(
            id INTEGER,
            name TEXT,
            salary REAL
        )
    """))

    conn.execute(text("""
        INSERT INTO employees VALUES
        (1,'Alice',100000),
        (2,'Bob',125000),
        (3,'Charlie',95000)
    """))

    conn.commit()

    rows = conn.execute(text("""
        SELECT *
        FROM employees
        ORDER BY salary DESC
    """)).fetchall()

    print("CORE TEST")

    for row in rows:
        print(row)
