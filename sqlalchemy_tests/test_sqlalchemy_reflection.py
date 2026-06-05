from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import text

engine = create_engine("sqlite:///:memory:")

with engine.begin() as conn:

    conn.execute(text("""
        CREATE TABLE employees(
            id INTEGER,
            name TEXT
        )
    """))

metadata = MetaData()

employees = Table(
    "employees",
    metadata,
    autoload_with=engine
)

print("REFLECTION TEST")
print(list(employees.columns.keys()))
