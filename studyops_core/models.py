from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Track(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    type: str
    created_at: datetime = Field(default_factory=utc_now)


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key='track.id')
    filename: str
    deeptutor_kb_name: str | None = None
    status: str = 'pending'
    created_at: datetime = Field(default_factory=utc_now)


class QuizAttempt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key='track.id')
    score: float | None = None
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class WeakTopic(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key='track.id')
    topic: str
    confidence: float = 0.0
    evidence: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=utc_now)


class StudyTask(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int | None = Field(default=None, foreign_key='track.id')
    title: str
    status: str = 'pending'
    due_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Plan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int | None = Field(default=None, foreign_key='track.id')
    title: str
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class Proposal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    risk_level: str
    status: str = 'pending'
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    rationale: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class AutonomyJob(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: str = 'pending'
    job_type: str
    input_snapshot: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    output: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class ApprovalRequest(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    proposal_id: int = Field(foreign_key='proposal.id')
    status: str = 'pending'
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class EventLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    event_type: str
    actor: str
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
