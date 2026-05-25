from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    display_name: str
    education_level: str = 'university'
    major: str | None = None
    semester: str | None = None
    timezone: str = 'Asia/Ho_Chi_Minh'
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Track(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = 'usr_local'
    type: str
    title: str
    description: str | None = None
    priority: str = 'medium'
    created_at: datetime = Field(default_factory=utc_now)


class Goal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key='track.id')
    title: str
    description: str | None = None
    success_criteria: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Deadline(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key='track.id')
    title: str
    due_at: datetime
    type: str = 'personal'
    importance: str = 'medium'
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class KnowledgeItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key='track.id')
    title: str
    source_type: str = 'pdf'
    source_uri: str | None = None
    deeptutor_kb_id: str | None = None
    deeptutor_document_id: str | None = None
    status: str = 'pending'
    created_at: datetime = Field(default_factory=utc_now)


class Quiz(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key='track.id')
    title: str
    source_knowledge_item_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    topic_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    difficulty: str = 'medium'
    question_count: int = 10
    deeptutor_quiz_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class QuizAttempt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    quiz_id: int = Field(foreign_key='quiz.id')
    track_id: int = Field(foreign_key='track.id')
    user_id: str = 'usr_local'
    score: float | None = None
    correct_count: int | None = None
    total_count: int | None = None
    mistake_topic_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    deeptutor_attempt_id: str | None = None
    feedback_summary: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class WeakTopic(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key='track.id')
    topic: str
    severity: str = 'low'
    confidence: float = 0.0
    evidence_event_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
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
