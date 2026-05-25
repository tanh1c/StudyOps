# StudyOps Mentor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local-first StudyOps Mentor MVP that connects StudyOps Core, DeepTutor, Hermes Agent, and 9Router into one evidence-backed learning loop for university students.

**Architecture:** StudyOps Core is a FastAPI control plane with SQLite state, adapter interfaces for DeepTutor/Hermes/9Router, and a simple Web Shell. DeepTutor owns document/RAG/quiz internals, Hermes owns mentor reasoning/autonomy output, and StudyOps Core owns product state, policies, approvals, and execution.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel, SQLite, pytest, httpx, React/Vite or minimal FastAPI-served frontend, Docker Compose, adapter mocks for external services.

---

## Implementation Rules

- Build phase-by-phase. Do not start Hermes/OpenClaw first.
- Use TDD for every backend behavior.
- Prefer mock adapters before real integrations.
- Keep high-risk autonomy actions blocked in MVP.
- Every state-changing operation writes an `EventLog`.
- Commit after each completed task group.
- Do not merge/fork upstream repos in MVP.

---

## Reference Repo Findings / Adapter Adjustments

These findings come from the local read-only reference repos in `external/` and should guide real adapter implementation after the mock phase.

### 9Router

Relevant files:

- `external/9router/README.md`
- `external/9router/DOCKER.md`
- `external/9router/.env.example`
- `external/9router/skills/9router-chat/SKILL.md`

Confirmed contract:

```text
Dashboard: http://localhost:20128/dashboard
OpenAI-compatible base URL: http://localhost:20128/v1
Chat endpoint: POST /v1/chat/completions
Model list: GET /v1/models
Embedding models: GET /v1/models/embedding
Docker image: decolua/9router:latest
Required env: JWT_SECRET, INITIAL_PASSWORD, DATA_DIR
Recommended env: PORT=20128, BASE_URL=http://localhost:20128
```

Implementation adjustment:

- `RouterAdapter.health_check()` should first call `GET {base_url}/models`.
- `UserSettings.llm_gateway_base_url` default remains `http://localhost:20128/v1`.
- Future Docker Compose should use published image `decolua/9router:latest` and map `20128:20128`.

### DeepTutor

Relevant files:

- `external/DeepTutor/AGENTS.md`
- `external/DeepTutor/deeptutor/api/run_server.py`
- `external/DeepTutor/deeptutor/api/main.py`
- `external/DeepTutor/deeptutor/api/routers/knowledge.py`
- `external/DeepTutor/deeptutor/api/routers/chat.py`
- `external/DeepTutor/deeptutor/api/routers/unified_ws.py`

Confirmed contract:

```text
Start server: deeptutor serve --port 8001
Backend app: deeptutor.api.main:app
Knowledge router prefix: /api/v1/knowledge
Chat WebSocket: /api/v1/chat
Unified WebSocket: /api/v1/ws
Knowledge health: GET /api/v1/knowledge/health
Create KB: POST /api/v1/knowledge/create (multipart form: name, files, rag_provider)
Upload to KB: POST /api/v1/knowledge/{kb_name}/upload (multipart form: files, rag_provider optional)
List KBs: GET /api/v1/knowledge/list
KB progress: GET /api/v1/knowledge/{kb_name}/progress
Task stream: GET /api/v1/knowledge/tasks/{task_id}/stream
Chat with RAG: WebSocket /api/v1/chat with message payload including kb_name and enable_rag=true
```

Important payload clues:

```json
{
  "message": "Apriori khác FP-Growth ở đâu?",
  "session_id": null,
  "kb_name": "data-mining",
  "enable_rag": true,
  "enable_web_search": false,
  "language": "vi"
}
```

Implementation adjustment:

- `DeepTutorAdapter.create_or_get_kb()` should create a sanitized KB name, not expect opaque `kb_id` first.
- `DeepTutorAdapter.upload_document()` must use multipart upload to `/api/v1/knowledge/{kb_name}/upload` or `/api/v1/knowledge/create`.
- `DeepTutorAdapter.ask_document()` is likely WebSocket-based via `/api/v1/chat`, not simple REST.
- The implementation plan should keep `MockDeepTutorAdapter` first, then add a real adapter with WebSocket support.
- The original `deeptutor_kb_id` field can hold the DeepTutor KB name for MVP.
- Quiz generation may not have a dedicated REST route; first real integration should implement RAG ask/document chat, then inspect capabilities/tools for quiz workflow or call DeepTutor CLI/capability layer.

### Hermes Agent

Relevant files:

- `external/hermes-agent/.env.example`
- `external/hermes-agent/README.md`
- `external/hermes-agent/hermes_cli/config.py`
- `external/hermes-agent/.plans/openai-api-server.md`

Confirmed contract:

```text
Hermes config lives under ~/.hermes/config.yaml and ~/.hermes/.env
Provider base URLs can be configured via env/config.
OPENAI_API_KEY and OPENAI_BASE_URL are recognized config/env keys.
Hermes has a planned OpenAI-compatible API server, not a clearly confirmed production endpoint in this checkout.
Planned API server would expose:
- POST /v1/chat/completions
- GET /v1/models
- GET /health
with local default around http://localhost:8642/v1 if enabled.
```

Implementation adjustment:

- Do not assume Hermes has a ready HTTP adapter at `localhost:9000`.
- Keep `MockHermesAdapter` as the default for MVP Phase 5/6.
- Real Hermes integration should be a separate spike before replacing the mock.
- Candidate real integration paths:
  1. Use Hermes CLI/non-interactive command if available.
  2. Enable/build Hermes OpenAI-compatible API server if current release supports it.
  3. Write a small StudyOps-specific Hermes skill/tool wrapper later.
- For 9Router integration, configure Hermes via `OPENAI_BASE_URL=http://localhost:20128/v1` and `OPENAI_API_KEY=<9router key>` if using OpenAI-compatible provider mode.

### Plan changes from these findings

- Phase 3 mock adapters remain correct and necessary.
- Phase 4 real DeepTutor integration should prioritize KB upload + RAG WebSocket before quiz.
- Phase 5/6 should not depend on real Hermes HTTP server until a Hermes integration spike confirms the endpoint.
- Add a new implementation spike before replacing mocks:

```text
Spike A: Real DeepTutor Adapter
- verify auth disabled/default local behavior
- call GET /api/v1/knowledge/health
- create/upload KB with multipart form
- connect to ws://localhost:8001/api/v1/chat
- send RAG message with enable_rag=true
- normalize streamed result/citations into StudyOps answer schema

Spike B: Real Hermes Adapter
- inspect installed Hermes CLI commands
- verify whether API_SERVER_ENABLED=true works in this version
- if API server works, call /health and /v1/chat/completions
- if not, keep mock and design a CLI wrapper or StudyOps-specific skill
```

---

## Phase 0 — Project Bootstrap

### Task 0.1: Create project skeleton

**Files:**
- Create: `studyops_core/__init__.py`
- Create: `studyops_core/main.py`
- Create: `studyops_core/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_health.py`
- Create: `pyproject.toml`
- Create: `.env.example`

**Step 1: Write failing health test**

```python
# tests/test_health.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_health_returns_ok():
    client = TestClient(app)
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
```

**Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_health.py -v
```

Expected: FAIL because `studyops_core.main` or `/health` does not exist yet.

**Step 3: Implement minimal FastAPI app**

```python
# studyops_core/main.py
from fastapi import FastAPI

app = FastAPI(title='StudyOps Core')


@app.get('/health')
def health():
    return {'status': 'ok'}
```

**Step 4: Add minimal config**

```python
# studyops_core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = 'sqlite:///./studyops.db'
    deeptutor_base_url: str = 'http://localhost:8001'
    hermes_base_url: str = 'http://localhost:9000'
    router_base_url: str = 'http://localhost:20128/v1'

    class Config:
        env_file = '.env'


settings = Settings()
```

**Step 5: Add project metadata**

```toml
# pyproject.toml
[project]
name = "studyops"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "sqlmodel",
  "pydantic-settings",
  "httpx",
  "python-multipart",
  "apscheduler"
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```env
# .env.example
DATABASE_URL=sqlite:///./studyops.db
DEEPTUTOR_BASE_URL=http://localhost:8001
HERMES_BASE_URL=http://localhost:9000
ROUTER_BASE_URL=http://localhost:20128/v1
```

**Step 6: Run test to verify it passes**

Run:

```bash
pytest tests/test_health.py -v
```

Expected: PASS.

**Step 7: Commit**

```bash
git add pyproject.toml .env.example studyops_core tests
git commit -m "feat: bootstrap StudyOps Core FastAPI app"
```

---

## Phase 1 — Core Database and Domain Models

### Task 1.1: Add database session and model base

**Files:**
- Create: `studyops_core/db.py`
- Create: `tests/test_db.py`

**Step 1: Write failing DB initialization test**

```python
# tests/test_db.py
from sqlmodel import SQLModel, Session, select

from studyops_core.db import create_db_and_tables, engine


def test_database_initializes():
    create_db_and_tables()
    with Session(engine) as session:
        result = session.exec(select(1)).one()
    assert result == 1
```

**Step 2: Run test**

```bash
pytest tests/test_db.py -v
```

Expected: FAIL because `studyops_core.db` does not exist.

**Step 3: Implement DB module**

```python
# studyops_core/db.py
from sqlmodel import SQLModel, create_engine

from studyops_core.config import settings

engine = create_engine(settings.database_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

**Step 4: Run test**

```bash
pytest tests/test_db.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add studyops_core/db.py tests/test_db.py
git commit -m "feat: add SQLite database initialization"
```

---

### Task 1.2: Add core domain models

**Files:**
- Create: `studyops_core/models.py`
- Create: `tests/test_models.py`

**Step 1: Write model tests**

```python
# tests/test_models.py
from studyops_core.models import Track, WeakTopic, AgentProposal


def test_track_requires_type_and_title():
    track = Track(user_id='user_1', type='course', title='Data Mining')
    assert track.type == 'course'
    assert track.status == 'active'


def test_weak_topic_has_evidence_list_default():
    weak_topic = WeakTopic(track_id='track_1', topic='support-confidence')
    assert weak_topic.evidence_event_ids == []
    assert weak_topic.status == 'active'


def test_agent_proposal_requires_rationale_shape():
    proposal = AgentProposal(
        user_id='user_1',
        proposal_type='create_tasks',
        title='Add practice task',
        summary='Add one practice task',
        rationale='Quiz score was low',
        proposed_changes={'create_tasks': []},
    )
    assert proposal.risk_level == 'low'
```

**Step 2: Run test**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL because models do not exist.

**Step 3: Implement models**

```python
# studyops_core/models.py
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def new_id(prefix: str) -> str:
    return f'{prefix}_{uuid4().hex[:12]}'


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class UserProfile(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('usr'), primary_key=True)
    display_name: str
    education_level: str = 'university'
    major: str | None = None
    semester: str | None = None
    timezone: str = 'Asia/Ho_Chi_Minh'
    active_track_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class LearningPreference(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('pref'), primary_key=True)
    user_id: str
    explanation_style: str = 'step_by_step'
    preferred_language: str = 'vi'
    daily_study_minutes_target: int = 75
    preferred_study_time: str | None = None
    difficulty_preference: str = 'balanced'
    feedback_style: str = 'coach_like'


class Track(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('trk'), primary_key=True)
    user_id: str
    type: str
    title: str
    description: str | None = None
    status: str = 'active'
    priority: str = 'medium'
    start_date: date | None = None
    target_date: date | None = None
    source: str = 'manual'
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Goal(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('goal'), primary_key=True)
    track_id: str
    title: str
    description: str | None = None
    success_criteria: str | None = None
    status: str = 'not_started'
    target_date: date | None = None
    confidence: float | None = None
    created_by: str = 'user'
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class Deadline(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('ddl'), primary_key=True)
    track_id: str
    title: str
    due_at: datetime
    type: str = 'personal'
    importance: str = 'medium'
    status: str = 'upcoming'
    source: str = 'manual'
    notes: str | None = None


class KnowledgeItem(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('kn'), primary_key=True)
    track_id: str
    title: str
    source_type: str = 'pdf'
    source_uri: str | None = None
    deeptutor_kb_id: str | None = None
    deeptutor_document_id: str | None = None
    status: str = 'processing'
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    uploaded_at: datetime = Field(default_factory=now_utc)


class Quiz(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('quiz'), primary_key=True)
    track_id: str
    title: str
    source_knowledge_item_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    topic_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    difficulty: str = 'medium'
    question_count: int = 10
    deeptutor_quiz_id: str | None = None
    created_by: str = 'user'
    created_at: datetime = Field(default_factory=now_utc)


class QuizAttempt(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('qa'), primary_key=True)
    quiz_id: str
    track_id: str
    user_id: str
    score: float
    correct_count: int
    total_count: int
    duration_seconds: int | None = None
    mistake_topic_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    deeptutor_attempt_id: str | None = None
    feedback_summary: str | None = None
    completed_at: datetime = Field(default_factory=now_utc)


class WeakTopic(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('wt'), primary_key=True)
    track_id: str
    topic: str
    source: str = 'quiz'
    severity: str = 'medium'
    confidence: float = 0.7
    evidence_event_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    last_seen_at: datetime = Field(default_factory=now_utc)
    status: str = 'active'


class StudyPlan(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('plan'), primary_key=True)
    user_id: str
    track_id: str | None = None
    scope: str = 'single_track'
    title: str
    start_date: date
    end_date: date
    status: str = 'draft'
    created_by: str = 'user'
    rationale: str | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class StudyTask(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('task'), primary_key=True)
    plan_id: str | None = None
    track_id: str
    title: str
    description: str | None = None
    task_type: str = 'review'
    scheduled_for: date | None = None
    estimated_minutes: int | None = None
    status: str = 'todo'
    priority: str = 'medium'
    linked_knowledge_item_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    linked_quiz_id: str | None = None
    created_by: str = 'user'


class EventLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('evt'), primary_key=True)
    user_id: str | None = None
    track_id: str | None = None
    event_type: str
    actor: str
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=now_utc)


class AutonomyJob(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('job'), primary_key=True)
    user_id: str
    job_type: str
    status: str = 'scheduled'
    scheduled_for: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    input_snapshot: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    output_summary: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=now_utc)


class AgentProposal(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('prop'), primary_key=True)
    user_id: str
    source_job_id: str | None = None
    proposal_type: str
    title: str
    summary: str
    rationale: str
    evidence_event_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    proposed_changes: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    risk_level: str = 'low'
    status: str = 'pending'
    created_at: datetime = Field(default_factory=now_utc)


class ApprovalRequest(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('appr'), primary_key=True)
    proposal_id: str
    user_id: str
    required_for: str
    status: str = 'pending'
    user_response: str | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=now_utc)
    resolved_at: datetime | None = None


class AutonomyPolicy(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('pol'), primary_key=True)
    user_id: str
    autonomy_level: str = 'L4'
    allow_auto_create_tasks: bool = True
    allow_auto_create_quizzes: bool = True
    allow_auto_update_weak_topics: bool = True
    require_approval_for_plan_changes: bool = True
    require_approval_for_priority_changes: bool = True
    require_approval_for_external_actions: bool = True
    weekly_review_enabled: bool = True
    daily_checkin_enabled: bool = True


class UserSettings(SQLModel, table=True):
    id: str = Field(default_factory=lambda: new_id('set'), primary_key=True)
    user_id: str
    llm_gateway_base_url: str = 'http://localhost:20128/v1'
    default_chat_model: str = 'default'
    default_reasoning_model: str | None = None
    default_embedding_model: str | None = None
    notification_channels: list[str] = Field(default_factory=lambda: ['in_app'], sa_column=Column(JSON))
    data_retention_days: int | None = None
    telemetry_enabled: bool = False
```

**Step 4: Ensure DB imports models before create_all**

```python
# studyops_core/db.py
from sqlmodel import SQLModel, create_engine

from studyops_core.config import settings
from studyops_core import models  # noqa: F401

engine = create_engine(settings.database_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

**Step 5: Run tests**

```bash
pytest tests/test_models.py tests/test_db.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add studyops_core/models.py studyops_core/db.py tests/test_models.py
git commit -m "feat: add StudyOps domain models"
```

---

### Task 1.3: Add event writer service

**Files:**
- Create: `studyops_core/services/events.py`
- Create: `tests/test_events.py`

**Step 1: Write failing event writer test**

```python
# tests/test_events.py
from sqlmodel import Session, select

from studyops_core.models import EventLog
from studyops_core.services.events import write_event


def test_write_event_persists_event(session: Session):
    event = write_event(
        session=session,
        event_type='track.created',
        actor='user',
        payload={'track_id': 'trk_1'},
        user_id='usr_1',
        track_id='trk_1',
    )

    saved = session.exec(select(EventLog).where(EventLog.id == event.id)).one()
    assert saved.event_type == 'track.created'
    assert saved.payload == {'track_id': 'trk_1'}
```

**Step 2: Add test fixture**

```python
# tests/conftest.py
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from studyops_core import models  # noqa: F401


@pytest.fixture
def session():
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

**Step 3: Run test**

```bash
pytest tests/test_events.py -v
```

Expected: FAIL because service does not exist.

**Step 4: Implement event writer**

```python
# studyops_core/services/events.py
from typing import Any

from sqlmodel import Session

from studyops_core.models import EventLog


def write_event(
    *,
    session: Session,
    event_type: str,
    actor: str,
    payload: dict[str, Any] | None = None,
    user_id: str | None = None,
    track_id: str | None = None,
) -> EventLog:
    event = EventLog(
        user_id=user_id,
        track_id=track_id,
        event_type=event_type,
        actor=actor,
        payload=payload or {},
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
```

**Step 5: Run test**

```bash
pytest tests/test_events.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add tests/conftest.py tests/test_events.py studyops_core/services/events.py
git commit -m "feat: add event log writer"
```

---

## Phase 2 — Core APIs and Onboarding

### Task 2.1: Add DB session dependency

**Files:**
- Modify: `studyops_core/db.py`
- Create: `studyops_core/deps.py`

**Step 1: Add dependency**

```python
# studyops_core/deps.py
from collections.abc import Generator

from sqlmodel import Session

from studyops_core.db import engine


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

**Step 2: Update app startup**

```python
# studyops_core/main.py
from fastapi import FastAPI

from studyops_core.db import create_db_and_tables

app = FastAPI(title='StudyOps Core')


@app.on_event('startup')
def on_startup():
    create_db_and_tables()


@app.get('/health')
def health():
    return {'status': 'ok'}
```

**Step 3: Run tests**

```bash
pytest -v
```

Expected: PASS.

**Step 4: Commit**

```bash
git add studyops_core/deps.py studyops_core/main.py
git commit -m "feat: add database session dependency"
```

---

### Task 2.2: Add profile and settings API

**Files:**
- Create: `studyops_core/schemas.py`
- Create: `studyops_core/routers/profile.py`
- Modify: `studyops_core/main.py`
- Create: `tests/test_profile_api.py`

**Step 1: Write failing API test**

```python
# tests/test_profile_api.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_create_or_update_profile():
    client = TestClient(app)
    response = client.put('/profile', json={
        'display_name': 'Long',
        'education_level': 'university',
        'major': 'Computer Science',
        'semester': 'Year 3',
        'timezone': 'Asia/Ho_Chi_Minh',
    })

    assert response.status_code == 200
    data = response.json()
    assert data['display_name'] == 'Long'
    assert data['major'] == 'Computer Science'
```

**Step 2: Run test**

```bash
pytest tests/test_profile_api.py -v
```

Expected: FAIL with 404.

**Step 3: Add schema and router**

```python
# studyops_core/schemas.py
from pydantic import BaseModel


class UserProfileUpsert(BaseModel):
    display_name: str
    education_level: str = 'university'
    major: str | None = None
    semester: str | None = None
    timezone: str = 'Asia/Ho_Chi_Minh'
```

```python
# studyops_core/routers/profile.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from studyops_core.deps import get_session
from studyops_core.models import UserProfile
from studyops_core.schemas import UserProfileUpsert
from studyops_core.services.events import write_event

router = APIRouter()


@router.get('/profile')
def get_profile(session: Session = Depends(get_session)):
    return session.exec(select(UserProfile)).first()


@router.put('/profile')
def upsert_profile(payload: UserProfileUpsert, session: Session = Depends(get_session)):
    profile = session.exec(select(UserProfile)).first()
    if profile is None:
        profile = UserProfile(**payload.model_dump())
        session.add(profile)
        session.commit()
        session.refresh(profile)
        write_event(session=session, event_type='profile.created', actor='user', user_id=profile.id, payload={'profile_id': profile.id})
        return profile

    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    write_event(session=session, event_type='profile.updated', actor='user', user_id=profile.id, payload={'profile_id': profile.id})
    return profile
```

**Step 4: Include router**

```python
# studyops_core/main.py
from fastapi import FastAPI

from studyops_core.db import create_db_and_tables
from studyops_core.routers import profile

app = FastAPI(title='StudyOps Core')
app.include_router(profile.router)
```

**Step 5: Run test**

```bash
pytest tests/test_profile_api.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add studyops_core/schemas.py studyops_core/routers/profile.py studyops_core/main.py tests/test_profile_api.py
git commit -m "feat: add profile API"
```

---

### Task 2.3: Add tracks, goals, and deadlines API

**Files:**
- Modify: `studyops_core/schemas.py`
- Create: `studyops_core/routers/tracks.py`
- Modify: `studyops_core/main.py`
- Create: `tests/test_tracks_api.py`

**Step 1: Write failing track API test**

```python
# tests/test_tracks_api.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_create_track_goal_and_deadline():
    client = TestClient(app)
    track_response = client.post('/tracks', json={
        'user_id': 'usr_local',
        'type': 'course',
        'title': 'Data Mining',
        'priority': 'high',
    })
    assert track_response.status_code == 200
    track = track_response.json()

    goal_response = client.post(f"/tracks/{track['id']}/goals", json={
        'title': 'Score 8/10 on midterm',
        'success_criteria': '>=80% quiz score before exam',
    })
    assert goal_response.status_code == 200

    deadline_response = client.post(f"/tracks/{track['id']}/deadlines", json={
        'title': 'Data Mining Midterm',
        'due_at': '2026-06-15T08:00:00+07:00',
        'type': 'exam',
        'importance': 'critical',
    })
    assert deadline_response.status_code == 200
```

**Step 2: Run test**

```bash
pytest tests/test_tracks_api.py -v
```

Expected: FAIL with 404.

**Step 3: Implement schemas**

```python
# add to studyops_core/schemas.py
from datetime import datetime


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
```

**Step 4: Implement router**

```python
# studyops_core/routers/tracks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from studyops_core.deps import get_session
from studyops_core.models import Deadline, Goal, Track
from studyops_core.schemas import DeadlineCreate, GoalCreate, TrackCreate
from studyops_core.services.events import write_event

router = APIRouter()


@router.get('/tracks')
def list_tracks(session: Session = Depends(get_session)):
    return session.exec(select(Track)).all()


@router.post('/tracks')
def create_track(payload: TrackCreate, session: Session = Depends(get_session)):
    track = Track(**payload.model_dump())
    session.add(track)
    session.commit()
    session.refresh(track)
    write_event(session=session, event_type='track.created', actor='user', user_id=track.user_id, track_id=track.id, payload={'track_id': track.id})
    return track


@router.get('/tracks/{track_id}')
def get_track(track_id: str, session: Session = Depends(get_session)):
    track = session.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail='Track not found')
    return track


@router.post('/tracks/{track_id}/goals')
def create_goal(track_id: str, payload: GoalCreate, session: Session = Depends(get_session)):
    if session.get(Track, track_id) is None:
        raise HTTPException(status_code=404, detail='Track not found')
    goal = Goal(track_id=track_id, **payload.model_dump())
    session.add(goal)
    session.commit()
    session.refresh(goal)
    write_event(session=session, event_type='goal.created', actor='user', track_id=track_id, payload={'goal_id': goal.id})
    return goal


@router.post('/tracks/{track_id}/deadlines')
def create_deadline(track_id: str, payload: DeadlineCreate, session: Session = Depends(get_session)):
    if session.get(Track, track_id) is None:
        raise HTTPException(status_code=404, detail='Track not found')
    deadline = Deadline(track_id=track_id, **payload.model_dump())
    session.add(deadline)
    session.commit()
    session.refresh(deadline)
    write_event(session=session, event_type='deadline.created', actor='user', track_id=track_id, payload={'deadline_id': deadline.id})
    return deadline
```

**Step 5: Include router**

```python
# studyops_core/main.py
from studyops_core.routers import profile, tracks

app.include_router(profile.router)
app.include_router(tracks.router)
```

**Step 6: Run tests**

```bash
pytest tests/test_tracks_api.py -v
```

Expected: PASS.

**Step 7: Commit**

```bash
git add studyops_core/schemas.py studyops_core/routers/tracks.py studyops_core/main.py tests/test_tracks_api.py
git commit -m "feat: add tracks goals and deadlines API"
```

---

## Phase 3 — Adapter Layer and Health Checks

### Task 3.1: Add adapter interfaces and mock adapters

**Files:**
- Create: `studyops_core/adapters/base.py`
- Create: `studyops_core/adapters/mock.py`
- Create: `tests/test_mock_adapters.py`

**Step 1: Write failing mock adapter tests**

```python
# tests/test_mock_adapters.py
from studyops_core.adapters.mock import MockDeepTutorAdapter, MockHermesAdapter, MockRouterAdapter


def test_mock_deeptutor_ask_returns_citations():
    adapter = MockDeepTutorAdapter()
    result = adapter.ask_document(kb_id='kb_1', question='Apriori là gì?', language='vi')
    assert result['answer']
    assert result['citations']


def test_mock_hermes_weekly_review_returns_proposals():
    adapter = MockHermesAdapter()
    result = adapter.run_weekly_review({'active_tracks': []})
    assert 'proposals' in result


def test_mock_router_health_is_ok():
    adapter = MockRouterAdapter()
    assert adapter.health_check()['status'] == 'ok'
```

**Step 2: Run test**

```bash
pytest tests/test_mock_adapters.py -v
```

Expected: FAIL.

**Step 3: Implement adapters**

```python
# studyops_core/adapters/base.py
from typing import Protocol


class DeepTutorAdapter(Protocol):
    def ask_document(self, *, kb_id: str, question: str, language: str) -> dict: ...
    def generate_quiz(self, payload: dict) -> dict: ...
    def grade_quiz(self, payload: dict) -> dict: ...


class HermesAdapter(Protocol):
    def run_daily_checkin(self, snapshot: dict) -> dict: ...
    def run_weekly_review(self, snapshot: dict) -> dict: ...
    def run_plan_rebalance(self, snapshot: dict, instruction: str) -> dict: ...


class RouterAdapter(Protocol):
    def health_check(self) -> dict: ...
```

```python
# studyops_core/adapters/mock.py
class MockDeepTutorAdapter:
    def create_or_get_kb(self, track: dict) -> dict:
        return {'deeptutor_kb_id': f"dt_kb_{track['id']}"}

    def upload_document(self, *, track_id: str, kb_id: str, file_path: str, title: str) -> dict:
        return {'deeptutor_document_id': 'dt_doc_mock', 'status': 'ready'}

    def ask_document(self, *, kb_id: str, question: str, language: str) -> dict:
        return {
            'answer': f'Mock answer for: {question}',
            'citations': [{'document_id': 'dt_doc_mock', 'title': 'Mock Lecture', 'page': 1, 'snippet': 'Mock citation'}],
            'session_id': 'dt_session_mock',
        }

    def generate_quiz(self, payload: dict) -> dict:
        return {
            'deeptutor_quiz_id': 'dt_quiz_mock',
            'questions': [
                {'id': 'q1', 'type': 'multiple_choice', 'question': 'Mock question?', 'choices': ['A', 'B'], 'topic_tags': ['support-confidence']}
            ],
        }

    def grade_quiz(self, payload: dict) -> dict:
        return {
            'deeptutor_attempt_id': 'dt_attempt_mock',
            'score': 55,
            'correct_count': 1,
            'total_count': 2,
            'question_results': [],
            'mistake_topic_tags': ['support-confidence'],
            'feedback_summary': 'Mock feedback',
        }


class MockHermesAdapter:
    def run_daily_checkin(self, snapshot: dict) -> dict:
        return {'job_summary': 'Mock daily checkin', 'messages': [], 'proposals': []}

    def run_weekly_review(self, snapshot: dict) -> dict:
        return {'job_summary': 'Mock weekly review', 'observations': [], 'track_assessments': [], 'proposals': []}

    def run_plan_rebalance(self, snapshot: dict, instruction: str) -> dict:
        return {'job_summary': f'Mock rebalance: {instruction}', 'proposals': []}


class MockRouterAdapter:
    def health_check(self) -> dict:
        return {'status': 'ok', 'models': ['mock-model']}
```

**Step 4: Run tests**

```bash
pytest tests/test_mock_adapters.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add studyops_core/adapters tests/test_mock_adapters.py
git commit -m "feat: add service adapter interfaces and mocks"
```

---

### Task 3.2: Add service health API

**Files:**
- Create: `studyops_core/routers/health.py`
- Modify: `studyops_core/main.py`
- Create: `tests/test_services_health.py`

**Step 1: Write failing test**

```python
# tests/test_services_health.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_services_health_returns_service_statuses():
    client = TestClient(app)
    response = client.get('/health/services')

    assert response.status_code == 200
    data = response.json()
    assert data['studyops_core'] == 'ok'
    assert data['router'] == 'ok'
```

**Step 2: Implement router with mock router adapter**

```python
# studyops_core/routers/health.py
from fastapi import APIRouter

from studyops_core.adapters.mock import MockRouterAdapter

router = APIRouter()


@router.get('/health/services')
def services_health():
    router_status = MockRouterAdapter().health_check()['status']
    return {
        'studyops_core': 'ok',
        'deeptutor': 'mock',
        'hermes': 'mock',
        'router': router_status,
    }
```

**Step 3: Include router**

```python
# studyops_core/main.py
from studyops_core.routers import health, profile, tracks

app.include_router(health.router)
```

**Step 4: Run test**

```bash
pytest tests/test_services_health.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add studyops_core/routers/health.py studyops_core/main.py tests/test_services_health.py
git commit -m "feat: add service health endpoint"
```

---

## Phase 4 — Knowledge, Quiz, and Weak Topics

### Task 4.1: Add knowledge upload and ask APIs using mock DeepTutor

**Files:**
- Create: `studyops_core/routers/knowledge.py`
- Modify: `studyops_core/main.py`
- Create: `tests/test_knowledge_api.py`

**Step 1: Write failing ask-document flow test**

```python
# tests/test_knowledge_api.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_upload_and_ask_knowledge_item():
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()

    upload = client.post(f"/tracks/{track['id']}/knowledge/upload", json={'title': 'Lecture 3', 'source_type': 'pdf'})
    assert upload.status_code == 200
    knowledge = upload.json()
    assert knowledge['status'] == 'ready'

    ask = client.post(f"/knowledge/{knowledge['id']}/ask", json={'question': 'Apriori là gì?', 'language': 'vi'})
    assert ask.status_code == 200
    assert ask.json()['citations']
```

**Step 2: Implement schemas**

```python
# add to studyops_core/schemas.py
class KnowledgeUpload(BaseModel):
    title: str
    source_type: str = 'pdf'
    source_uri: str | None = None


class KnowledgeAsk(BaseModel):
    question: str
    language: str = 'vi'
    include_mentor_guidance: bool = True
```

**Step 3: Implement router**

```python
# studyops_core/routers/knowledge.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from studyops_core.adapters.mock import MockDeepTutorAdapter
from studyops_core.deps import get_session
from studyops_core.models import KnowledgeItem, Track
from studyops_core.schemas import KnowledgeAsk, KnowledgeUpload
from studyops_core.services.events import write_event

router = APIRouter()


@router.post('/tracks/{track_id}/knowledge/upload')
def upload_knowledge(track_id: str, payload: KnowledgeUpload, session: Session = Depends(get_session)):
    track = session.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail='Track not found')

    adapter = MockDeepTutorAdapter()
    kb = adapter.create_or_get_kb(track.model_dump())
    doc = adapter.upload_document(track_id=track_id, kb_id=kb['deeptutor_kb_id'], file_path=payload.source_uri or '', title=payload.title)

    item = KnowledgeItem(
        track_id=track_id,
        title=payload.title,
        source_type=payload.source_type,
        source_uri=payload.source_uri,
        deeptutor_kb_id=kb['deeptutor_kb_id'],
        deeptutor_document_id=doc['deeptutor_document_id'],
        status=doc['status'],
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    write_event(session=session, event_type='knowledge.uploaded', actor='user', track_id=track_id, payload={'knowledge_item_id': item.id})
    return item


@router.post('/knowledge/{knowledge_item_id}/ask')
def ask_knowledge(knowledge_item_id: str, payload: KnowledgeAsk, session: Session = Depends(get_session)):
    item = session.get(KnowledgeItem, knowledge_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Knowledge item not found')
    if item.status != 'ready':
        raise HTTPException(status_code=409, detail='Knowledge item is not ready')

    result = MockDeepTutorAdapter().ask_document(kb_id=item.deeptutor_kb_id or '', question=payload.question, language=payload.language)
    write_event(session=session, event_type='knowledge.asked', actor='user', track_id=item.track_id, payload={'knowledge_item_id': item.id, 'question': payload.question})
    return {**result, 'mentor_guidance': None, 'knowledge_query_id': None}
```

**Step 4: Include router and run test**

```python
# studyops_core/main.py
from studyops_core.routers import health, knowledge, profile, tracks

app.include_router(knowledge.router)
```

Run:

```bash
pytest tests/test_knowledge_api.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add studyops_core/schemas.py studyops_core/routers/knowledge.py studyops_core/main.py tests/test_knowledge_api.py
git commit -m "feat: add knowledge upload and ask flow"
```

---

### Task 4.2: Add quiz generation and attempt APIs

**Files:**
- Create: `studyops_core/routers/quizzes.py`
- Modify: `studyops_core/main.py`
- Create: `tests/test_quiz_api.py`

**Step 1: Write failing quiz lifecycle test**

```python
# tests/test_quiz_api.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_generate_and_attempt_quiz_updates_weak_topic():
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()
    quiz_response = client.post(f"/tracks/{track['id']}/quizzes/generate", json={
        'knowledge_item_ids': [],
        'topic_tags': ['apriori'],
        'difficulty': 'medium',
        'question_count': 2,
        'language': 'vi',
    })
    assert quiz_response.status_code == 200
    quiz = quiz_response.json()

    attempt_response = client.post(f"/quizzes/{quiz['id']}/attempts", json={'answers': [{'question_id': 'q1', 'answer': 'B'}]})
    assert attempt_response.status_code == 200
    attempt = attempt_response.json()
    assert attempt['score'] == 55
    assert attempt['weak_topics_updated']
```

**Step 2: Add schemas**

```python
# add to studyops_core/schemas.py
class QuizGenerate(BaseModel):
    knowledge_item_ids: list[str] = []
    topic_tags: list[str] = []
    difficulty: str = 'medium'
    question_count: int = 10
    language: str = 'vi'


class QuizAttemptCreate(BaseModel):
    answers: list[dict]
```

**Step 3: Add weak topic service**

```python
# studyops_core/services/weak_topics.py
from sqlmodel import Session, select

from studyops_core.models import WeakTopic


def severity_from_score(score: float) -> str:
    if score < 50:
        return 'high'
    if score < 70:
        return 'medium'
    return 'low'


def update_weak_topics_from_quiz(*, session: Session, track_id: str, topics: list[str], score: float, evidence_event_id: str) -> list[WeakTopic]:
    updated = []
    severity = severity_from_score(score)
    for topic in topics:
        weak_topic = session.exec(select(WeakTopic).where(WeakTopic.track_id == track_id, WeakTopic.topic == topic)).first()
        if weak_topic is None:
            weak_topic = WeakTopic(track_id=track_id, topic=topic, severity=severity, evidence_event_ids=[evidence_event_id])
        else:
            weak_topic.severity = severity
            weak_topic.evidence_event_ids = list(set(weak_topic.evidence_event_ids + [evidence_event_id]))
        session.add(weak_topic)
        updated.append(weak_topic)
    session.commit()
    for item in updated:
        session.refresh(item)
    return updated
```

**Step 4: Implement quiz router**

```python
# studyops_core/routers/quizzes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from studyops_core.adapters.mock import MockDeepTutorAdapter
from studyops_core.deps import get_session
from studyops_core.models import Quiz, QuizAttempt, Track
from studyops_core.schemas import QuizAttemptCreate, QuizGenerate
from studyops_core.services.events import write_event
from studyops_core.services.weak_topics import update_weak_topics_from_quiz

router = APIRouter()


@router.post('/tracks/{track_id}/quizzes/generate')
def generate_quiz(track_id: str, payload: QuizGenerate, session: Session = Depends(get_session)):
    if session.get(Track, track_id) is None:
        raise HTTPException(status_code=404, detail='Track not found')
    result = MockDeepTutorAdapter().generate_quiz(payload.model_dump())
    quiz = Quiz(
        track_id=track_id,
        title='Generated quiz',
        source_knowledge_item_ids=payload.knowledge_item_ids,
        topic_tags=payload.topic_tags,
        difficulty=payload.difficulty,
        question_count=payload.question_count,
        deeptutor_quiz_id=result['deeptutor_quiz_id'],
    )
    session.add(quiz)
    session.commit()
    session.refresh(quiz)
    write_event(session=session, event_type='quiz.generated', actor='user', track_id=track_id, payload={'quiz_id': quiz.id})
    return quiz


@router.post('/quizzes/{quiz_id}/attempts')
def attempt_quiz(quiz_id: str, payload: QuizAttemptCreate, session: Session = Depends(get_session)):
    quiz = session.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail='Quiz not found')
    result = MockDeepTutorAdapter().grade_quiz({'deeptutor_quiz_id': quiz.deeptutor_quiz_id, 'answers': payload.answers})
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        track_id=quiz.track_id,
        user_id='usr_local',
        score=result['score'],
        correct_count=result['correct_count'],
        total_count=result['total_count'],
        mistake_topic_tags=result['mistake_topic_tags'],
        deeptutor_attempt_id=result['deeptutor_attempt_id'],
        feedback_summary=result['feedback_summary'],
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    event = write_event(session=session, event_type='quiz.attempt.completed', actor='user', track_id=quiz.track_id, payload={'quiz_attempt_id': attempt.id, 'score': attempt.score})
    weak_topics = update_weak_topics_from_quiz(session=session, track_id=quiz.track_id, topics=attempt.mistake_topic_tags, score=attempt.score, evidence_event_id=event.id)
    return {**attempt.model_dump(), 'weak_topics_updated': [topic.id for topic in weak_topics]}
```

**Step 5: Include router and run tests**

```python
# studyops_core/main.py
from studyops_core.routers import health, knowledge, profile, quizzes, tracks

app.include_router(quizzes.router)
```

Run:

```bash
pytest tests/test_quiz_api.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add studyops_core/schemas.py studyops_core/services/weak_topics.py studyops_core/routers/quizzes.py studyops_core/main.py tests/test_quiz_api.py
git commit -m "feat: add quiz attempts and weak topic updates"
```

---

## Phase 5 — Planning, Tasks, and Daily Coach

### Task 5.1: Add task APIs

**Files:**
- Create: `studyops_core/routers/tasks.py`
- Modify: `studyops_core/main.py`
- Create: `tests/test_tasks_api.py`

**Step 1: Write failing task lifecycle test**

```python
# tests/test_tasks_api.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_create_complete_and_skip_task():
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()
    task_response = client.post('/tasks', json={
        'track_id': track['id'],
        'title': 'Review Apriori',
        'task_type': 'review',
        'estimated_minutes': 25,
    })
    assert task_response.status_code == 200
    task = task_response.json()

    complete = client.post(f"/tasks/{task['id']}/complete")
    assert complete.status_code == 200
    assert complete.json()['status'] == 'done'
```

**Step 2: Add schema**

```python
# add to studyops_core/schemas.py
from datetime import date


class StudyTaskCreate(BaseModel):
    track_id: str
    title: str
    description: str | None = None
    task_type: str = 'review'
    scheduled_for: date | None = None
    estimated_minutes: int | None = None
    priority: str = 'medium'
    created_by: str = 'user'
```

**Step 3: Implement router**

```python
# studyops_core/routers/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from studyops_core.deps import get_session
from studyops_core.models import StudyTask, Track
from studyops_core.schemas import StudyTaskCreate
from studyops_core.services.events import write_event

router = APIRouter()


@router.post('/tasks')
def create_task(payload: StudyTaskCreate, session: Session = Depends(get_session)):
    if session.get(Track, payload.track_id) is None:
        raise HTTPException(status_code=404, detail='Track not found')
    task = StudyTask(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    write_event(session=session, event_type='study_task.created', actor=task.created_by, track_id=task.track_id, payload={'task_id': task.id})
    return task


@router.get('/tracks/{track_id}/tasks')
def list_track_tasks(track_id: str, session: Session = Depends(get_session)):
    return session.exec(select(StudyTask).where(StudyTask.track_id == track_id)).all()


@router.post('/tasks/{task_id}/complete')
def complete_task(task_id: str, session: Session = Depends(get_session)):
    task = session.get(StudyTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    task.status = 'done'
    session.add(task)
    session.commit()
    session.refresh(task)
    write_event(session=session, event_type='study_task.completed', actor='user', track_id=task.track_id, payload={'task_id': task.id})
    return task


@router.post('/tasks/{task_id}/skip')
def skip_task(task_id: str, session: Session = Depends(get_session)):
    task = session.get(StudyTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    task.status = 'skipped'
    session.add(task)
    session.commit()
    session.refresh(task)
    write_event(session=session, event_type='study_task.skipped', actor='user', track_id=task.track_id, payload={'task_id': task.id})
    return task
```

**Step 4: Include router and run tests**

```python
# studyops_core/main.py
from studyops_core.routers import health, knowledge, profile, quizzes, tasks, tracks

app.include_router(tasks.router)
```

Run:

```bash
pytest tests/test_tasks_api.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add studyops_core/schemas.py studyops_core/routers/tasks.py studyops_core/main.py tests/test_tasks_api.py
git commit -m "feat: add study task API"
```

---

### Task 5.2: Add daily checkin autonomy job with mock Hermes

**Files:**
- Create: `studyops_core/services/autonomy.py`
- Create: `studyops_core/routers/autonomy.py`
- Modify: `studyops_core/main.py`
- Create: `tests/test_daily_checkin.py`

**Step 1: Write failing test**

```python
# tests/test_daily_checkin.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_run_daily_checkin_creates_job():
    client = TestClient(app)
    response = client.post('/autonomy/jobs/run', json={'job_type': 'daily_checkin', 'reason': 'manual_run'})

    assert response.status_code == 200
    data = response.json()
    assert data['job_type'] == 'daily_checkin'
    assert data['status'] == 'succeeded'
```

**Step 2: Add schema**

```python
# add to studyops_core/schemas.py
class AutonomyRunRequest(BaseModel):
    job_type: str
    reason: str = 'manual_run'
```

**Step 3: Implement autonomy service**

```python
# studyops_core/services/autonomy.py
from datetime import datetime, timezone

from sqlmodel import Session, select

from studyops_core.adapters.mock import MockHermesAdapter
from studyops_core.models import AutonomyJob, Track
from studyops_core.services.events import write_event


def run_daily_checkin(*, session: Session, user_id: str = 'usr_local') -> AutonomyJob:
    job = AutonomyJob(user_id=user_id, job_type='daily_checkin', status='running', scheduled_for=datetime.now(timezone.utc), started_at=datetime.now(timezone.utc))
    session.add(job)
    session.commit()
    session.refresh(job)

    tracks = session.exec(select(Track).where(Track.status == 'active')).all()
    snapshot = {'active_tracks': [track.model_dump() for track in tracks]}
    output = MockHermesAdapter().run_daily_checkin(snapshot)

    job.input_snapshot = snapshot
    job.output_summary = output.get('job_summary')
    job.status = 'succeeded'
    job.completed_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    session.refresh(job)
    write_event(session=session, event_type='daily_checkin.completed', actor='hermes', user_id=user_id, payload={'job_id': job.id})
    return job
```

**Step 4: Implement router**

```python
# studyops_core/routers/autonomy.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from studyops_core.deps import get_session
from studyops_core.schemas import AutonomyRunRequest
from studyops_core.services.autonomy import run_daily_checkin

router = APIRouter()


@router.post('/autonomy/jobs/run')
def run_autonomy_job(payload: AutonomyRunRequest, session: Session = Depends(get_session)):
    if payload.job_type == 'daily_checkin':
        return run_daily_checkin(session=session)
    raise HTTPException(status_code=400, detail='Unsupported job type')
```

**Step 5: Include router and run test**

```python
# studyops_core/main.py
from studyops_core.routers import autonomy, health, knowledge, profile, quizzes, tasks, tracks

app.include_router(autonomy.router)
```

Run:

```bash
pytest tests/test_daily_checkin.py -v
```

Expected: PASS.

**Step 6: Commit**

```bash
git add studyops_core/schemas.py studyops_core/services/autonomy.py studyops_core/routers/autonomy.py studyops_core/main.py tests/test_daily_checkin.py
git commit -m "feat: add daily checkin autonomy job"
```

---

## Phase 6 — Policy, Proposals, Approvals, Weekly Review

### Task 6.1: Add policy classifier

**Files:**
- Create: `studyops_core/services/policy.py`
- Create: `tests/test_policy.py`

**Step 1: Write failing policy tests**

```python
# tests/test_policy.py
from studyops_core.services.policy import classify_action


def test_create_small_task_is_auto():
    decision = classify_action({'type': 'create_small_task'})
    assert decision == 'auto'


def test_modify_active_plan_requires_approval():
    decision = classify_action({'type': 'modify_active_plan'})
    assert decision == 'approval'


def test_shell_command_is_blocked():
    decision = classify_action({'type': 'shell_command'})
    assert decision == 'blocked'
```

**Step 2: Implement classifier**

```python
# studyops_core/services/policy.py
AUTO_ACTIONS = {
    'create_small_task',
    'create_practice_quiz',
    'update_weak_topic_evidence',
    'send_in_app_notification',
    'summarize_progress',
}

APPROVAL_ACTIONS = {
    'modify_active_plan',
    'reschedule_many_tasks',
    'adjust_track_priority',
    'mark_goal_at_risk',
    'replace_weekly_plan',
    'drop_task',
}

BLOCKED_ACTIONS = {
    'delete_data',
    'external_message',
    'submit_assignment',
    'shell_command',
    'external_account_action',
}


def classify_action(action: dict) -> str:
    action_type = action['type']
    if action_type in BLOCKED_ACTIONS:
        return 'blocked'
    if action_type in APPROVAL_ACTIONS:
        return 'approval'
    if action_type in AUTO_ACTIONS:
        return 'auto'
    return 'approval'
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_policy.py -v
git add studyops_core/services/policy.py tests/test_policy.py
git commit -m "feat: add autonomy policy classifier"
```

Expected: PASS and commit succeeds.

---

### Task 6.2: Add proposal validation and approval lifecycle

**Files:**
- Create: `studyops_core/services/proposals.py`
- Modify: `studyops_core/routers/autonomy.py`
- Create: `tests/test_proposals.py`

**Step 1: Write failing proposal test**

```python
# tests/test_proposals.py
from sqlmodel import Session, select

from studyops_core.models import AgentProposal, ApprovalRequest
from studyops_core.services.proposals import create_proposal_with_policy


def test_medium_risk_proposal_creates_approval(session: Session):
    proposal = create_proposal_with_policy(
        session=session,
        user_id='usr_local',
        proposal_type='modify_plan',
        title='Rebalance week',
        summary='Move project task later',
        rationale='Midterm is near',
        proposed_changes={'actions': [{'type': 'modify_active_plan'}]},
    )

    approval = session.exec(select(ApprovalRequest).where(ApprovalRequest.proposal_id == proposal.id)).one()
    assert proposal.status == 'pending'
    assert approval.status == 'pending'
```

**Step 2: Implement proposal service**

```python
# studyops_core/services/proposals.py
from sqlmodel import Session

from studyops_core.models import AgentProposal, ApprovalRequest
from studyops_core.services.events import write_event
from studyops_core.services.policy import classify_action


def create_proposal_with_policy(*, session: Session, user_id: str, proposal_type: str, title: str, summary: str, rationale: str, proposed_changes: dict, evidence_event_ids: list[str] | None = None) -> AgentProposal:
    actions = proposed_changes.get('actions', [])
    decisions = [classify_action(action) for action in actions] or ['approval']

    if 'blocked' in decisions:
        status = 'rejected'
        risk_level = 'high'
    elif 'approval' in decisions:
        status = 'pending'
        risk_level = 'medium'
    else:
        status = 'auto_applied'
        risk_level = 'low'

    proposal = AgentProposal(
        user_id=user_id,
        proposal_type=proposal_type,
        title=title,
        summary=summary,
        rationale=rationale,
        evidence_event_ids=evidence_event_ids or [],
        proposed_changes=proposed_changes,
        risk_level=risk_level,
        status=status,
    )
    session.add(proposal)
    session.commit()
    session.refresh(proposal)

    if status == 'pending':
        approval = ApprovalRequest(proposal_id=proposal.id, user_id=user_id, required_for=proposal_type)
        session.add(approval)
        session.commit()

    write_event(session=session, event_type='agent_proposal.created', actor='hermes', user_id=user_id, payload={'proposal_id': proposal.id, 'status': status})
    return proposal
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_proposals.py -v
git add studyops_core/services/proposals.py tests/test_proposals.py
git commit -m "feat: add proposal policy lifecycle"
```

Expected: PASS.

---

### Task 6.3: Add weekly review job with mock Hermes proposal

**Files:**
- Modify: `studyops_core/adapters/mock.py`
- Modify: `studyops_core/services/autonomy.py`
- Modify: `studyops_core/routers/autonomy.py`
- Create: `tests/test_weekly_review.py`

**Step 1: Write failing weekly review test**

```python
# tests/test_weekly_review.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_weekly_review_creates_pending_proposal():
    client = TestClient(app)
    response = client.post('/autonomy/jobs/run', json={'job_type': 'weekly_review', 'reason': 'manual_run'})

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'succeeded'

    proposals = client.get('/proposals').json()
    assert proposals
    assert proposals[0]['status'] == 'pending'
```

**Step 2: Update mock Hermes weekly output**

```python
# update MockHermesAdapter.run_weekly_review in studyops_core/adapters/mock.py
    def run_weekly_review(self, snapshot: dict) -> dict:
        return {
            'job_summary': 'Data Mining needs priority this week.',
            'observations': [],
            'track_assessments': [],
            'proposals': [
                {
                    'proposal_type': 'modify_plan',
                    'title': 'Prioritize Data Mining this week',
                    'summary': 'Move one project task later and add Data Mining review.',
                    'rationale': 'Midterm is close and quiz score is low.',
                    'evidence_event_ids': [],
                    'proposed_changes': {'actions': [{'type': 'modify_active_plan'}]},
                }
            ],
        }
```

**Step 3: Add weekly review service function**

```python
# add to studyops_core/services/autonomy.py
from studyops_core.services.proposals import create_proposal_with_policy


def run_weekly_review(*, session: Session, user_id: str = 'usr_local') -> AutonomyJob:
    job = AutonomyJob(user_id=user_id, job_type='weekly_review', status='running', scheduled_for=datetime.now(timezone.utc), started_at=datetime.now(timezone.utc))
    session.add(job)
    session.commit()
    session.refresh(job)

    tracks = session.exec(select(Track).where(Track.status == 'active')).all()
    snapshot = {'active_tracks': [track.model_dump() for track in tracks]}
    output = MockHermesAdapter().run_weekly_review(snapshot)

    for proposal_data in output.get('proposals', []):
        create_proposal_with_policy(session=session, user_id=user_id, **proposal_data)

    job.input_snapshot = snapshot
    job.output_summary = output.get('job_summary')
    job.status = 'succeeded'
    job.completed_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    session.refresh(job)
    write_event(session=session, event_type='weekly_review.completed', actor='hermes', user_id=user_id, payload={'job_id': job.id})
    return job
```

**Step 4: Add proposal API and weekly job route**

```python
# update studyops_core/routers/autonomy.py
from sqlmodel import select
from studyops_core.models import AgentProposal
from studyops_core.services.autonomy import run_daily_checkin, run_weekly_review


@router.post('/autonomy/jobs/run')
def run_autonomy_job(payload: AutonomyRunRequest, session: Session = Depends(get_session)):
    if payload.job_type == 'daily_checkin':
        return run_daily_checkin(session=session)
    if payload.job_type == 'weekly_review':
        return run_weekly_review(session=session)
    raise HTTPException(status_code=400, detail='Unsupported job type')


@router.get('/proposals')
def list_proposals(session: Session = Depends(get_session)):
    return session.exec(select(AgentProposal)).all()
```

**Step 5: Run tests and commit**

```bash
pytest tests/test_weekly_review.py -v
git add studyops_core/adapters/mock.py studyops_core/services/autonomy.py studyops_core/routers/autonomy.py tests/test_weekly_review.py
git commit -m "feat: add weekly review proposal flow"
```

Expected: PASS.

---

### Task 6.4: Add approve/reject endpoints

**Files:**
- Modify: `studyops_core/routers/autonomy.py`
- Create: `tests/test_approvals.py`

**Step 1: Write failing approval test**

```python
# tests/test_approvals.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_approve_proposal_marks_it_approved():
    client = TestClient(app)
    client.post('/autonomy/jobs/run', json={'job_type': 'weekly_review', 'reason': 'manual_run'})
    proposal = client.get('/proposals').json()[0]

    response = client.post(f"/proposals/{proposal['id']}/approve")
    assert response.status_code == 200
    assert response.json()['status'] == 'approved'
```

**Step 2: Implement endpoints**

```python
# add to studyops_core/routers/autonomy.py
@router.post('/proposals/{proposal_id}/approve')
def approve_proposal(proposal_id: str, session: Session = Depends(get_session)):
    proposal = session.get(AgentProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail='Proposal not found')
    proposal.status = 'approved'
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    write_event(session=session, event_type='approval.accepted', actor='user', user_id=proposal.user_id, payload={'proposal_id': proposal.id})
    return proposal


@router.post('/proposals/{proposal_id}/reject')
def reject_proposal(proposal_id: str, session: Session = Depends(get_session)):
    proposal = session.get(AgentProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail='Proposal not found')
    proposal.status = 'rejected'
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    write_event(session=session, event_type='approval.rejected', actor='user', user_id=proposal.user_id, payload={'proposal_id': proposal.id})
    return proposal
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_approvals.py -v
git add studyops_core/routers/autonomy.py tests/test_approvals.py
git commit -m "feat: add proposal approval endpoints"
```

Expected: PASS.

---

## Phase 7 — Web Shell MVP

### Task 7.1: Add minimal static Web Shell

**Files:**
- Create: `studyops_core/static/index.html`
- Modify: `studyops_core/main.py`
- Create: `tests/test_web_shell.py`

**Step 1: Write failing web shell test**

```python
# tests/test_web_shell.py
from fastapi.testclient import TestClient

from studyops_core.main import app


def test_web_shell_serves_index():
    client = TestClient(app)
    response = client.get('/ui')

    assert response.status_code == 200
    assert 'StudyOps Mentor' in response.text
```

**Step 2: Add minimal HTML**

```html
<!-- studyops_core/static/index.html -->
<!doctype html>
<html>
  <head>
    <title>StudyOps Mentor</title>
  </head>
  <body>
    <h1>StudyOps Mentor</h1>
    <p>Local-first study operating system.</p>
    <section id="service-health">Service health will appear here.</section>
    <section id="tracks">Tracks will appear here.</section>
    <section id="approvals">Approvals will appear here.</section>
  </body>
</html>
```

**Step 3: Serve static file**

```python
# add to studyops_core/main.py
from fastapi.responses import FileResponse


@app.get('/ui')
def web_shell():
    return FileResponse('studyops_core/static/index.html')
```

**Step 4: Run test and commit**

```bash
pytest tests/test_web_shell.py -v
git add studyops_core/static/index.html studyops_core/main.py tests/test_web_shell.py
git commit -m "feat: add minimal StudyOps web shell"
```

Expected: PASS.

---

## Phase 8 — Local Runtime and Demo Hardening

### Task 8.1: Add Docker Compose and run command docs

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `README.md`

**Step 1: Add Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .
COPY . /app

CMD ["uvicorn", "studyops_core.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Add Compose file**

```yaml
# docker-compose.yml
services:
  studyops-core:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
```

**Step 3: Add setup docs**

```markdown
# StudyOps Mentor

Local-first study operating system MVP.

## Run

```bash
cp .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:8000/ui
```
```

**Step 4: Verify manually**

Run:

```bash
docker compose up --build
```

Expected: app starts and `/health` returns `{"status":"ok"}`.

**Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml README.md
git commit -m "chore: add local Docker runtime"
```

---

### Task 8.2: Add golden demo seed script

**Files:**
- Create: `scripts/seed_demo.py`
- Create: `tests/test_seed_demo.py`

**Step 1: Write failing seed test**

```python
# tests/test_seed_demo.py
from scripts.seed_demo import build_demo_payload


def test_demo_payload_contains_three_tracks():
    payload = build_demo_payload()
    assert len(payload['tracks']) == 3
    assert {track['type'] for track in payload['tracks']} == {'course', 'project', 'career'}
```

**Step 2: Implement payload builder**

```python
# scripts/seed_demo.py
def build_demo_payload():
    return {
        'profile': {'display_name': 'Demo Student', 'education_level': 'university', 'major': 'Computer Science'},
        'tracks': [
            {'type': 'course', 'title': 'Data Mining', 'priority': 'high'},
            {'type': 'project', 'title': 'Portfolio RAG Chatbot', 'priority': 'medium'},
            {'type': 'career', 'title': 'AI Engineer Internship', 'priority': 'high'},
        ],
    }


if __name__ == '__main__':
    print(build_demo_payload())
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_seed_demo.py -v
git add scripts/seed_demo.py tests/test_seed_demo.py
git commit -m "chore: add golden demo seed payload"
```

Expected: PASS.

---

## Final Verification Checklist

Run all tests:

```bash
pytest -v
```

Expected: all tests pass.

Run local server:

```bash
uvicorn studyops_core.main:app --reload
```

Manual smoke test:

```text
1. Open http://localhost:8000/health
2. Open http://localhost:8000/ui
3. Create profile through API or UI.
4. Create Data Mining, RAG Chatbot, AI Internship tracks.
5. Upload mock knowledge item.
6. Ask document and verify citation response.
7. Generate quiz.
8. Attempt quiz and verify weak topic update.
9. Run daily_checkin.
10. Run weekly_review.
11. Approve proposal.
12. Check EventLog entries.
```

Demo API commands:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/services
curl -X POST http://localhost:8000/tracks -H 'Content-Type: application/json' -d '{"user_id":"usr_local","type":"course","title":"Data Mining"}'
curl -X POST http://localhost:8000/autonomy/jobs/run -H 'Content-Type: application/json' -d '{"job_type":"weekly_review","reason":"manual_run"}'
curl http://localhost:8000/proposals
```

---

## Post-MVP Follow-ups

After this plan succeeds:

```text
1. Replace MockDeepTutorAdapter with real DeepTutor API/CLI wrapper.
2. Replace MockHermesAdapter with real Hermes endpoint/custom tool call.
3. Replace static Web Shell with React/Vite UI.
4. Add browser notifications.
5. Add real file upload handling.
6. Add richer proposal diff execution.
7. Add Docker Compose entries for DeepTutor, Hermes, and 9Router.
8. Investigate OpenClaw only after core learning loop is stable.
```
