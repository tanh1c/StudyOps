from sqlmodel import Session, select

from studyops_core.db import create_db_and_tables, engine


def test_database_initializes():
    create_db_and_tables()
    with Session(engine) as session:
        result = session.exec(select(1)).one()
    assert result == 1
