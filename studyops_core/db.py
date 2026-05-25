from sqlmodel import SQLModel, create_engine

from studyops_core.config import settings

engine = create_engine(settings.database_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
