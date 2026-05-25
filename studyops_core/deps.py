from collections.abc import Generator

from sqlmodel import Session

from studyops_core.db import create_db_and_tables, engine


def get_session() -> Generator[Session, None, None]:
    create_db_and_tables()
    with Session(engine) as session:
        yield session
