from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine

from studyops_core.config import settings

engine = create_engine(settings.database_url, echo=False)


def create_db_and_tables():
    import studyops_core.models

    SQLModel.metadata.create_all(engine)
    ensure_local_schema()


def ensure_local_schema():
    if not settings.database_url.startswith('sqlite'):
        return

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    statements = []

    if 'track' in tables:
        track_columns = _table_columns(inspector, 'track')
        if 'user_id' not in track_columns:
            statements.append("ALTER TABLE track ADD COLUMN user_id VARCHAR DEFAULT 'usr_local'")

    if 'knowledgeitem' in tables:
        knowledge_columns = _table_columns(inspector, 'knowledgeitem')
        if 'deeptutor_task_id' not in knowledge_columns:
            statements.append('ALTER TABLE knowledgeitem ADD COLUMN deeptutor_task_id VARCHAR')
        if 'progress' not in knowledge_columns:
            statements.append("ALTER TABLE knowledgeitem ADD COLUMN progress JSON DEFAULT '{}'")

    if 'quiz' in tables:
        quiz_columns = _table_columns(inspector, 'quiz')
        if 'payload' not in quiz_columns:
            statements.append("ALTER TABLE quiz ADD COLUMN payload JSON DEFAULT '{}'")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _table_columns(inspector, table_name: str) -> set[str]:
    return {column['name'] for column in inspector.get_columns(table_name)}
