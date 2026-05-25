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
