from sqlalchemy import create_engine
from sqlalchemy import text

engine = create_engine("sqlite:///:memory:")

with engine.begin() as conn:

    conn.execute(text("""
        CREATE TABLE test(
            id INTEGER
        )
    """))

    conn.execute(text("""
        INSERT INTO test VALUES (1)
    """))

with engine.connect() as conn:

    count = conn.execute(
        text("SELECT COUNT(*) FROM test")
    ).scalar()

print("TRANSACTION TEST")
print("Rows:", count)
