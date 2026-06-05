from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

class Base(DeclarativeBase):
    pass

class Employee(Base):

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    salary: Mapped[float]

engine = create_engine("sqlite:///:memory:")

Base.metadata.create_all(engine)

with Session(engine) as session:

    session.add_all([
        Employee(id=1,name="Alice",salary=100000),
        Employee(id=2,name="Bob",salary=125000),
        Employee(id=3,name="Charlie",salary=95000),
    ])

    session.commit()

    rows = session.query(Employee)\
                  .order_by(Employee.salary.desc())\
                  .all()

    print("ORM TEST")

    for row in rows:
        print(row.id,row.name,row.salary)
