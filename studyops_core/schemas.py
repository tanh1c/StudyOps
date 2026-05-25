from datetime import datetime

from pydantic import BaseModel


class UserProfileUpsert(BaseModel):
    display_name: str
    education_level: str = 'university'
    major: str | None = None
    semester: str | None = None
    timezone: str = 'Asia/Ho_Chi_Minh'


class TrackCreate(BaseModel):
    user_id: str = 'usr_local'
    type: str
    title: str
    description: str | None = None
    priority: str = 'medium'


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    success_criteria: str | None = None


class DeadlineCreate(BaseModel):
    title: str
    due_at: datetime
    type: str = 'personal'
    importance: str = 'medium'
    notes: str | None = None


class KnowledgeUpload(BaseModel):
    title: str
    source_type: str = 'pdf'
    source_uri: str | None = None


class KnowledgeAsk(BaseModel):
    question: str
    language: str = 'vi'
    include_mentor_guidance: bool = True


class QuizGenerate(BaseModel):
    knowledge_item_ids: list[int] = []
    topic_tags: list[str] = []
    difficulty: str = 'medium'
    question_count: int = 10
    language: str = 'vi'


class QuizAttemptCreate(BaseModel):
    answers: list[dict]
