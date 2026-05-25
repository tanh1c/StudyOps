# StudyOps Mentor Design

Date: 2026-05-25
Status: Draft

## Context

This design is based on `raw_idea.md` and the brainstorming decisions made so far.

Confirmed decisions:

- Product: StudyOps Mentor
- Target user: university students managing multiple courses, projects, and internship/career preparation
- Deployment: local-first, self-hosted by each user
- Primary UI: Web UI, initially using DeepTutor frontend / UI surface
- Integration style: glue-only, not merging upstream codebases
- Architecture direction: StudyOps as Control Plane
- Autonomy target: L4 autonomous worker
- Timeline: 8-12 weeks

---

## Section 1 — Product Definition + Architecture Tổng Thể

### Product name tạm thời

**StudyOps Mentor**

Một **local-first AI mentor cho sinh viên đại học** giúp quản lý:

- nhiều môn học cùng lúc,
- project cá nhân / project môn học,
- định hướng internship / career,
- tài liệu học tập,
- quiz / weak topics,
- roadmap học tập,
- daily coaching,
- weekly autonomous review.

Điểm khác biệt không phải là “chatbot giải bài”, mà là:

> Mentor biết bạn đang học môn gì, deadline nào đang tới, project nào đang kẹt, bạn yếu phần nào, tuần này nên ưu tiên gì, và tự chạy review định kỳ để đề xuất điều chỉnh kế hoạch.

### Core positioning

StudyOps không nên tự định vị là:

- “AI Tutor” đơn thuần,
- “RAG app”,
- “agent framework”,
- “task manager”,
- “OpenAI wrapper”.

Nên định vị là:

> **Personal Study Operating System for university students.**

Hoặc tiếng Việt:

> **Hệ điều hành học tập cá nhân cho sinh viên.**

Trong đó:

```text
DeepTutor = giáo viên / tutor chuyên môn
Hermes = mentor cá nhân / autonomous agent
9Router = model gateway
StudyOps Core = control plane / source of truth
```

### Architecture chính

```text
User
 ↓
DeepTutor Web UI / StudyOps Web Shell
 ↓
StudyOps Core
 - user profile
 - tracks
 - goals
 - deadlines
 - study plans
 - weak topics
 - quiz attempts
 - event log
 - approval queue
 - autonomy jobs
 ↓
┌───────────────────────────────┐
│ External local services        │
├───────────────────────────────┤
│ Hermes Agent                   │
│ - mentor conversation          │
│ - L4 autonomous worker         │
│ - scheduled jobs               │
│ - plan/review reasoning        │
│                               │
│ DeepTutor                      │
│ - document workspace           │
│ - RAG Q&A                      │
│ - quiz generation              │
│ - problem solving              │
│ - tutoring flows               │
│                               │
│ 9Router                        │
│ - OpenAI-compatible endpoint   │
│ - provider routing             │
│ - fallback                     │
│ - cost/token control           │
└───────────────────────────────┘
 ↓
LLM providers / embedding providers
```

StudyOps Core **không thay thế** Hermes/DeepTutor/9Router. Nó chỉ làm 3 việc:

1. **Normalize state**  
   Mọi dữ liệu quan trọng được lưu có schema rõ ràng: track, goal, deadline, quiz result, weak topic, study session, action log.

2. **Coordinate services**  
   Khi user tạo quiz, StudyOps gọi DeepTutor. Khi đến weekly review, StudyOps gọi Hermes. Khi cần LLM, các service đi qua 9Router.

3. **Guard autonomy**  
   L4 agent không được tự ý sửa mọi thứ. Nó phải tạo proposal/action trước, StudyOps Core quyết định auto-apply hay cần user approve.

### Vai trò từng repo

#### 1. 9Router — Model Gateway

Vai trò:

```text
Một endpoint LLM thống nhất cho toàn bộ hệ thống.
```

Dùng cho:

- Hermes gọi LLM,
- DeepTutor gọi LLM,
- embedding / reranking nếu compatible,
- fallback provider,
- cost control,
- token tracking.

Không nên dùng 9Router như “linh hồn sản phẩm”. Nó là infrastructure.

#### 2. DeepTutor — Education Engine

Vai trò:

```text
Service chuyên về học tập/tutoring.
```

Dùng cho:

- upload tài liệu,
- tạo knowledge base,
- RAG Q&A có citation,
- giải bài từng bước,
- sinh quiz,
- chấm / giải thích quiz,
- guided learning path ở cấp topic/chapter.

DeepTutor không nên là source of truth cho toàn bộ user life. Nó chỉ biết “học liệu và hoạt động học”.

#### 3. Hermes Agent — Mentor + Autonomous Worker

Vai trò:

```text
Agent sống lâu, biết goal, biết context, biết schedule, biết gọi tools.
```

Dùng cho:

- conversation mentor,
- daily check-in,
- weekly review,
- autonomous planning,
- gọi StudyOps Core như tool,
- gọi DeepTutor qua StudyOps Core,
- tạo proposal điều chỉnh roadmap,
- tổng hợp tiến độ.

Hermes không nên lưu state sản phẩm chính một cách opaque. Memory của Hermes dùng để personalize conversation, còn dữ liệu quan trọng vẫn nằm trong StudyOps Core.

#### 4. StudyOps Core — Control Plane

Đây là phần tự build.

Vai trò:

```text
Source of truth + API bridge + autonomy guardrail.
```

Nó quản lý:

- users,
- tracks,
- goals,
- deadlines,
- documents metadata,
- study plans,
- tasks,
- quiz attempts,
- weak topics,
- events,
- autonomy jobs,
- approval requests,
- settings.

Nếu một ngày bỏ Hermes để dùng OpenClaw, hoặc bỏ DeepTutor để dùng engine khác, StudyOps Core vẫn giữ được product data.

### Local-first deployment

MVP chạy bằng Docker Compose:

```text
studyops-core        localhost:8000
deeptutor-backend    localhost:8001
deeptutor-frontend   localhost:3782
hermes-agent         localhost:9000 hoặc CLI/daemon
9router              localhost:20128/v1
postgres/sqlite      local volume
vector db            local volume
```

User experience mong muốn:

```text
1. User clone StudyOps
2. Chạy setup script
3. Nhập API keys/provider config
4. Mở localhost
5. Upload tài liệu
6. Tạo tracks: môn học, project, internship goal
7. Mentor bắt đầu daily/weekly coaching
```

### MVP full scope đã chốt

Vì timeline **8-12 tuần**, MVP có thể gồm:

#### Must-have

1. **Knowledge Workspace**
   - upload PDF/slide/notes,
   - gắn document vào track,
   - hỏi đáp theo tài liệu,
   - citation.

2. **Quiz + Weak Topic Tracking**
   - sinh quiz từ tài liệu/chapter/topic,
   - user trả lời,
   - chấm,
   - giải thích lỗi sai,
   - cập nhật weak topics.

3. **Mentor Memory + Daily Coach**
   - lưu mục tiêu,
   - deadline,
   - learning style,
   - daily recommended tasks,
   - conversation context.

4. **Multi-track**
   - course track,
   - project track,
   - career/internship track.

5. **L4 Autonomous Worker**
   - weekly review,
   - tự phân tích tiến độ,
   - tự đề xuất điều chỉnh roadmap,
   - tự sinh next-week plan,
   - một số action low-risk có thể auto-apply,
   - medium/high-risk phải xin approval.

### Nguyên tắc thiết kế quan trọng

#### 1. “One product, many services”

Không merge codebase. Nhưng user vẫn thấy một sản phẩm.

```text
Codebase: modular
UX: unified enough
State: centralized in StudyOps Core
```

#### 2. “Autonomy with receipts”

Mọi hành động agent làm phải có log:

```text
Agent did X
Because Y
Based on data Z
At time T
Result R
```

Không có black box autonomy.

#### 3. “Proposal before mutation”

Với các thay đổi quan trọng:

```text
Hermes không sửa roadmap trực tiếp.
Hermes tạo proposal.
StudyOps Core lưu proposal.
User approve/reject.
Sau đó mới apply.
```

#### 4. “Tracks are first-class”

Vì target là sinh viên đa môn + project + internship, mọi thứ phải gắn với track:

```text
document → track
quiz → track
weak topic → track
deadline → track
study task → track
weekly review → nhiều track
```

Nếu không làm vậy, multi-track sẽ thành một đống context lẫn lộn.

---

## Section 2 — Data Model / Domain Objects

StudyOps Core is the control plane, so the data model must keep product state inspectable and testable. Hermes can reason, and DeepTutor can tutor, but StudyOps Core must own the durable state.

### 2.1 Entity map tổng thể

```text
UserProfile
 ├── LearningPreference
 ├── Track[]
 │    ├── Goal[]
 │    ├── Deadline[]
 │    ├── KnowledgeItem[]
 │    ├── StudyPlan[]
 │    │    └── StudyTask[]
 │    ├── Quiz[]
 │    │    └── QuizAttempt[]
 │    ├── WeakTopic[]
 │    └── ProjectArtifact[]
 │
 ├── ConversationMemory[]
 ├── StudySession[]
 ├── EventLog[]
 ├── AutonomyJob[]
 ├── AgentProposal[]
 ├── ApprovalRequest[]
 └── Settings
```

Key rules:

- `UserProfile` represents the local learner.
- `Track` is a separate goal stream: course, project, or career/internship.
- Important data should be linked to `track_id` whenever possible.
- `EventLog` is the backbone for autonomy and debugging.
- `AgentProposal` and `ApprovalRequest` prevent unsafe direct mutation by the agent.

### 2.2 Core entities

#### `UserProfile`

Represents one local user. MVP can be single-user, but keeping this entity makes future multi-user/cloud migration easier.

```ts
UserProfile {
  id: string
  display_name: string
  education_level: "university" | "high_school" | "self_learner"
  major?: string
  semester?: string
  timezone: string
  active_track_ids: string[]
  created_at: datetime
  updated_at: datetime
}
```

#### `LearningPreference`

Structured learning preferences used by Hermes and DeepTutor.

```ts
LearningPreference {
  id: string
  user_id: string
  explanation_style: "short" | "step_by_step" | "socratic" | "example_first"
  preferred_language: "vi" | "en" | "mixed"
  daily_study_minutes_target: number
  preferred_study_time?: string
  difficulty_preference: "easy_first" | "balanced" | "challenge_me"
  feedback_style: "gentle" | "direct" | "coach_like"
}
```

#### `Track`

The central entity for multi-track learning.

```ts
Track {
  id: string
  user_id: string
  type: "course" | "project" | "career"
  title: string
  description?: string
  status: "active" | "paused" | "completed" | "archived"
  priority: "low" | "medium" | "high" | "critical"
  start_date?: date
  target_date?: date
  source?: "manual" | "syllabus" | "mentor_suggested"
  created_at: datetime
  updated_at: datetime
}
```

Example tracks:

```json
{ "type": "course", "title": "Data Mining", "priority": "high", "target_date": "2026-07-10" }
{ "type": "project", "title": "Portfolio RAG Chatbot", "priority": "medium", "target_date": "2026-08-01" }
{ "type": "career", "title": "Prepare for AI Engineer Internship", "priority": "high", "target_date": "2026-09-01" }
```

#### `Goal`

A concrete objective inside a track.

```ts
Goal {
  id: string
  track_id: string
  title: string
  description?: string
  success_criteria?: string
  status: "not_started" | "in_progress" | "achieved" | "dropped"
  target_date?: date
  confidence?: number
  created_by: "user" | "mentor" | "system"
  created_at: datetime
  updated_at: datetime
}
```

#### `Deadline`

A deadline for course, project, or career work.

```ts
Deadline {
  id: string
  track_id: string
  title: string
  due_at: datetime
  type: "exam" | "quiz" | "assignment" | "project_milestone" | "application" | "personal"
  importance: "low" | "medium" | "high" | "critical"
  status: "upcoming" | "done" | "missed" | "cancelled"
  source: "manual" | "syllabus" | "mentor_suggested"
  notes?: string
}
```

### 2.3 Knowledge / document entities

#### `KnowledgeItem`

Metadata about documents or learning sources. DeepTutor owns vector/RAG internals; StudyOps stores mapping and product context.

```ts
KnowledgeItem {
  id: string
  track_id: string
  title: string
  source_type: "pdf" | "slide" | "note" | "url" | "repo" | "manual"
  source_uri?: string
  deeptutor_kb_id?: string
  deeptutor_document_id?: string
  status: "processing" | "ready" | "failed" | "archived"
  tags: string[]
  uploaded_at: datetime
}
```

#### `KnowledgeQuery`

Stores important RAG interactions, not every chat token.

```ts
KnowledgeQuery {
  id: string
  track_id: string
  user_id: string
  question: string
  answer_summary?: string
  deeptutor_session_id?: string
  citation_count?: number
  created_at: datetime
}
```

### 2.4 Quiz / weak topic entities

#### `Quiz`

```ts
Quiz {
  id: string
  track_id: string
  title: string
  source_knowledge_item_ids: string[]
  topic_tags: string[]
  difficulty: "easy" | "medium" | "hard" | "mixed"
  question_count: number
  deeptutor_quiz_id?: string
  created_by: "user" | "mentor" | "autonomy_worker"
  created_at: datetime
}
```

#### `QuizAttempt`

```ts
QuizAttempt {
  id: string
  quiz_id: string
  track_id: string
  user_id: string
  score: number
  correct_count: number
  total_count: number
  duration_seconds?: number
  mistake_topic_tags: string[]
  deeptutor_attempt_id?: string
  feedback_summary?: string
  completed_at: datetime
}
```

#### `WeakTopic`

A topic the learner struggles with. Weak topics must have evidence.

```ts
WeakTopic {
  id: string
  track_id: string
  topic: string
  source: "quiz" | "self_report" | "mentor_inferred" | "knowledge_query"
  severity: "low" | "medium" | "high"
  confidence: number
  evidence_event_ids: string[]
  last_seen_at: datetime
  status: "active" | "improving" | "resolved" | "ignored"
}
```

### 2.5 Planning entities

#### `StudyPlan`

A plan for a single track or multiple tracks.

```ts
StudyPlan {
  id: string
  user_id: string
  track_id?: string
  scope: "single_track" | "multi_track"
  title: string
  start_date: date
  end_date: date
  status: "draft" | "active" | "completed" | "superseded"
  created_by: "user" | "mentor" | "autonomy_worker"
  rationale?: string
  created_at: datetime
  updated_at: datetime
}
```

#### `StudyTask`

```ts
StudyTask {
  id: string
  plan_id: string
  track_id: string
  title: string
  description?: string
  task_type: "read" | "practice" | "quiz" | "review" | "project_work" | "career_prep"
  scheduled_for?: date
  estimated_minutes?: number
  status: "todo" | "in_progress" | "done" | "skipped" | "rescheduled"
  priority: "low" | "medium" | "high"
  linked_knowledge_item_ids: string[]
  linked_quiz_id?: string
  created_by: "user" | "mentor" | "autonomy_worker"
}
```

#### `StudySession`

```ts
StudySession {
  id: string
  user_id: string
  track_id: string
  started_at: datetime
  ended_at?: datetime
  duration_minutes?: number
  activity_type: "reading" | "quiz" | "coding" | "writing" | "review" | "planning"
  linked_task_id?: string
  self_rating?: number
  notes?: string
}
```

### 2.6 Agent / autonomy entities

#### `EventLog`

Append-only log of important system events.

```ts
EventLog {
  id: string
  user_id: string
  track_id?: string
  event_type: string
  actor: "user" | "system" | "hermes" | "deeptutor" | "autonomy_worker"
  payload: json
  created_at: datetime
}
```

Important event types:

```text
track.created
deadline.created
knowledge.uploaded
quiz.generated
quiz.attempt.completed
weak_topic.created
study_task.completed
study_task.skipped
daily_checkin.sent
weekly_review.started
agent_proposal.created
approval.accepted
approval.rejected
```

#### `AutonomyJob`

A scheduled or event-triggered agent job.

```ts
AutonomyJob {
  id: string
  user_id: string
  job_type: "daily_checkin" | "weekly_review" | "deadline_watch" | "weak_topic_remediation" | "plan_rebalance"
  status: "scheduled" | "running" | "succeeded" | "failed" | "cancelled"
  scheduled_for: datetime
  started_at?: datetime
  completed_at?: datetime
  input_snapshot?: json
  output_summary?: string
  error_message?: string
  created_at: datetime
}
```

#### `AgentProposal`

The structured output of agent reasoning.

```ts
AgentProposal {
  id: string
  user_id: string
  source_job_id?: string
  proposal_type: "create_plan" | "modify_plan" | "create_tasks" | "adjust_priority" | "mark_goal_at_risk" | "create_quiz" | "update_weak_topic"
  title: string
  summary: string
  rationale: string
  evidence_event_ids: string[]
  proposed_changes: json
  risk_level: "low" | "medium" | "high"
  status: "pending" | "auto_applied" | "approved" | "rejected" | "expired"
  created_at: datetime
}
```

#### `ApprovalRequest`

```ts
ApprovalRequest {
  id: string
  proposal_id: string
  user_id: string
  required_for: "modify_plan" | "send_message" | "external_action" | "delete_data" | "major_priority_change"
  status: "pending" | "approved" | "rejected" | "expired"
  user_response?: string
  expires_at?: datetime
  created_at: datetime
  resolved_at?: datetime
}
```

Policy baseline:

```text
Low-risk:
- create small study tasks
- create quizzes
- update weak topics from quiz evidence
→ may auto-apply

Medium-risk:
- modify weekly roadmap
- shift priority across tracks
- mark goal at-risk
→ needs approval or semi-auto confirmation

High-risk:
- send email
- submit assignment
- delete data
- run shell command
- use external account
→ always needs explicit approval
```

#### `AgentMemoryNote`

Structured memory that StudyOps allows and can inspect.

```ts
AgentMemoryNote {
  id: string
  user_id: string
  track_id?: string
  memory_type: "preference" | "habit" | "constraint" | "personal_context" | "learning_pattern"
  content: string
  confidence: number
  source_event_ids: string[]
  status: "active" | "superseded" | "deleted"
  created_by: "hermes" | "user"
  created_at: datetime
  updated_at: datetime
}
```

### 2.7 Integration mapping entities

#### `ExternalServiceRef`

Mapping between StudyOps entities and external service IDs.

```ts
ExternalServiceRef {
  id: string
  entity_type: "knowledge_item" | "quiz" | "conversation" | "agent_job"
  entity_id: string
  service: "deeptutor" | "hermes" | "9router" | "openclaw"
  external_id: string
  metadata: json
  created_at: datetime
}
```

#### `ModelUsageLog`

```ts
ModelUsageLog {
  id: string
  user_id: string
  service: "hermes" | "deeptutor" | "studyops_core"
  provider?: string
  model?: string
  input_tokens?: number
  output_tokens?: number
  cost_estimate?: number
  request_type: "rag" | "quiz_generation" | "daily_checkin" | "weekly_review" | "mentor_chat"
  created_at: datetime
}
```

### 2.8 Settings / policy entities

#### `AutonomyPolicy`

```ts
AutonomyPolicy {
  id: string
  user_id: string
  autonomy_level: "L2" | "L3" | "L4"
  allow_auto_create_tasks: boolean
  allow_auto_create_quizzes: boolean
  allow_auto_update_weak_topics: boolean
  require_approval_for_plan_changes: boolean
  require_approval_for_priority_changes: boolean
  require_approval_for_external_actions: boolean
  weekly_review_enabled: boolean
  daily_checkin_enabled: boolean
}
```

Default MVP L4 policy:

```json
{
  "autonomy_level": "L4",
  "allow_auto_create_tasks": true,
  "allow_auto_create_quizzes": true,
  "allow_auto_update_weak_topics": true,
  "require_approval_for_plan_changes": true,
  "require_approval_for_priority_changes": true,
  "require_approval_for_external_actions": true,
  "weekly_review_enabled": true,
  "daily_checkin_enabled": true
}
```

L4 reasoning is enabled, but major mutation still needs approval.

#### `UserSettings`

```ts
UserSettings {
  id: string
  user_id: string
  llm_gateway_base_url: string
  default_chat_model: string
  default_reasoning_model?: string
  default_embedding_model?: string
  notification_channels: string[]
  data_retention_days?: number
  telemetry_enabled: boolean
}
```

Local-first default: `telemetry_enabled = false`.

### 2.9 Recommended database choice

For MVP local-first:

```text
StudyOps Core state: SQLite
Uploaded files: local filesystem
Vector/RAG: DeepTutor-managed
Long-term agent memory: SQLite + Hermes memory
```

Reasons:

- easy local setup,
- no Postgres requirement for single-user MVP,
- simple backup,
- portable,
- enough for local-first usage.

Future migration path:

```text
SQLite → Postgres
local filesystem → object storage
local vector store → managed vector DB
```

### 2.10 Minimal schema for MVP

Required MVP entities:

```text
UserProfile
LearningPreference
Track
Goal
Deadline
KnowledgeItem
Quiz
QuizAttempt
WeakTopic
StudyPlan
StudyTask
EventLog
AutonomyJob
AgentProposal
ApprovalRequest
AutonomyPolicy
UserSettings
```

Can be deferred:

```text
KnowledgeQuery
StudySession
AgentMemoryNote
ExternalServiceRef
ModelUsageLog
```

For serious L4 autonomy, these are non-negotiable:

```text
EventLog
AutonomyJob
AgentProposal
ApprovalRequest
AutonomyPolicy
```

Without them, L4 becomes an opaque agent running in the background.

### 2.11 Important relationships

```text
UserProfile 1 ── * Track

Track 1 ── * Goal
Track 1 ── * Deadline
Track 1 ── * KnowledgeItem
Track 1 ── * Quiz
Track 1 ── * WeakTopic
Track 1 ── * StudyTask

StudyPlan 1 ── * StudyTask

Quiz 1 ── * QuizAttempt

AutonomyJob 1 ── * AgentProposal
AgentProposal 0/1 ── 1 ApprovalRequest

EventLog * ── 0/1 Track
EventLog * ── 0/1 UserProfile
```

Enforce these rules:

- `QuizAttempt.track_id` duplicates `Quiz.track_id` for simpler queries.
- `StudyTask.track_id` is required, even for multi-track plans.
- `WeakTopic` always belongs to a track.
- `AgentProposal` must include `rationale` and, when possible, `evidence_event_ids`.
- `AutonomyJob.input_snapshot` should store the state snapshot used when the job ran.

### 2.12 Example end-to-end data flows

#### User performs poorly on a quiz → L4 proposes plan adjustment

```text
1. User completes Data Mining quiz.
2. DeepTutor returns result.
3. StudyOps creates QuizAttempt(score=55).
4. StudyOps creates EventLog(quiz.attempt.completed).
5. StudyOps updates WeakTopic("support-confidence", severity=high).
6. StudyOps creates EventLog(weak_topic.updated).
7. StudyOps triggers AutonomyJob(weak_topic_remediation).
8. Hermes reads QuizAttempt, WeakTopic, nearby Deadline, and current StudyPlan.
9. Hermes creates AgentProposal: add two association-rule practice tasks.
10. If low-risk, StudyOps auto-applies proposal.
11. Daily Coach shows the new tasks tomorrow.
```

#### Weekly multi-track review

```text
1. Sunday 20:00, AutonomyJob(weekly_review) runs.
2. StudyOps builds input_snapshot:
   - active tracks
   - deadlines in next 14 days
   - task completion
   - quiz scores
   - weak topics
   - study sessions
3. Hermes analyzes the snapshot.
4. Hermes creates AgentProposal:
   - Data Mining is high risk
   - chatbot project can move two tasks later
   - internship prep keeps one light task
5. Risk is medium because it changes priority across tracks.
6. StudyOps creates ApprovalRequest.
7. User approves.
8. StudyOps applies changes to StudyPlan/StudyTask.
9. EventLog records all changes.
```

### 2.13 Design decisions

Chốt các quyết định:

1. SQLite for StudyOps Core MVP.
2. `Track` is the central product entity.
3. Append-only `EventLog` is required.
4. L4 agent cannot mutate major state directly.
5. `AgentProposal` + `ApprovalRequest` are required guardrails.
6. `WeakTopic` must include evidence.
7. DeepTutor owns vector/RAG internals; StudyOps stores metadata and mapping.
8. Hermes memory personalizes conversation; StudyOps Core owns product state.

---

## Section 3 — User Flows

This section describes the product from the learner's point of view: onboarding, track setup, document upload, RAG Q&A, quiz loops, daily coaching, weekly review, and approvals.

### 3.1 North Star Flow

```text
1. User opens StudyOps for the first time.
2. User creates a learning profile.
3. User creates three tracks:
   - Course: Data Mining
   - Project: Portfolio RAG Chatbot
   - Career: AI Engineer Internship
4. User uploads documents for each track.
5. StudyOps/DeepTutor processes documents into knowledge bases.
6. Mentor asks about goals and deadlines.
7. Mentor creates a weekly plan.
8. Each day, user opens the app and sees:
   - what to study today
   - nearby deadlines
   - weak topics to practice
   - project tasks to work on
9. User asks documents, completes quizzes, and marks tasks done.
10. StudyOps records EventLog entries.
11. L4 worker runs weekly review.
12. Mentor proposes next-week plan changes.
13. User approves or rejects.
14. StudyOps updates the plan.
```

The loop is not just question-answering. It connects documents, activity, weak topics, deadlines, and planning into continuous learning guidance.

### 3.2 First-run onboarding flow

Goal: after first launch, the user should have a working model config, profile, at least one track, at least one goal/deadline, an autonomy policy, and one uploaded document.

```text
Open localhost
 ↓
Welcome screen
 ↓
Step 1: Setup model gateway
 ↓
Step 2: Create learner profile
 ↓
Step 3: Create first tracks
 ↓
Step 4: Add goals/deadlines
 ↓
Step 5: Configure autonomy policy
 ↓
Step 6: Upload first document
 ↓
Ready dashboard
```

#### Step 1 — Setup model gateway

User enters:

```text
9Router base URL
API key
default chat model
default reasoning model
default embedding model, if needed
```

Default local base URL:

```text
http://localhost:20128/v1
```

The app should provide a `Test model connection` button. If 9Router is unavailable, the user should see a clear service error and not proceed into AI-dependent flows.

#### Step 2 — Create learner profile

User enters:

```text
preferred name
major
year / semester
preferred language: vi / en / mixed
explanation style: short, step-by-step, example-first, Socratic
daily study target
preferred study time
```

Output:

```text
UserProfile
LearningPreference
```

#### Step 3 — Create first tracks

MVP supports three track types:

```text
Course
Project
Career
```

For each track, ask for:

```text
title
description
priority
target date
```

Output:

```text
Track
EventLog(track.created)
```

#### Step 4 — Add goals/deadlines

After each track is created, ask:

```text
Does this track have an upcoming deadline?
What does success look like for this track?
```

Example:

```text
Data Mining:
- Midterm 2026-06-15
- Goal: achieve >= 8/10 on midterm

RAG Chatbot:
- Demo MVP 2026-07-01
- Goal: deploy a demo with citations

AI Internship:
- Apply to 10 positions before 2026-08-01
- Goal: CV + 2 portfolio projects
```

Output:

```text
Goal
Deadline
EventLog(goal.created)
EventLog(deadline.created)
```

#### Step 5 — Configure autonomy policy

Default preset:

```text
Autonomy mode: Guided L4
```

User-facing explanation:

```text
StudyOps can automatically:
- create small study tasks
- create practice quizzes
- update weak topics based on quiz evidence
- run weekly reviews

StudyOps will ask before:
- changing your weekly roadmap
- changing priority across tracks
- sending anything outside the app
- deleting data
- running system commands
```

Output:

```text
AutonomyPolicy
EventLog(autonomy_policy.created)
```

#### Step 6 — Upload first document

```text
1. User selects a track and uploads a file.
2. StudyOps creates KnowledgeItem(status=processing).
3. StudyOps sends document to DeepTutor.
4. StudyOps stores deeptutor_kb_id / document_id.
5. StudyOps updates KnowledgeItem(status=ready).
6. StudyOps creates EventLog(knowledge.uploaded).
```

If processing fails:

```text
KnowledgeItem(status=failed)
EventLog(knowledge.processing_failed)
```

### 3.3 Daily dashboard flow

The dashboard should answer four questions:

```text
1. What should I do today?
2. Which deadlines are close?
3. What am I weak at?
4. Which agent proposals need approval?
```

MVP dashboard:

```text
[Today]
- 3 recommended tasks
- estimated time
- priority reason

[Tracks]
- Course: Data Mining — at risk / on track
- Project: RAG Chatbot — on track
- Career: AI Internship — slow

[Weak Topics]
- support-confidence — high
- vector search evaluation — medium

[Approvals]
- Weekly plan adjustment pending
```

Data sources:

```text
StudyTask
Deadline
WeakTopic
AgentProposal
ApprovalRequest
EventLog
```

Today tasks can come from existing `StudyPlan` tasks or from Hermes daily coach proposals. Low-risk task proposals may auto-apply.

### 3.4 Track workspace flow

A track workspace should show:

```text
Track Overview
- goal
- deadline
- risk status
- progress

Knowledge
- uploaded documents
- ask document
- generate quiz

Plan
- tasks this week
- completed/skipped tasks

Weak Topics
- topic
- severity
- evidence

Activity
- recent events
```

Course example:

```text
Data Mining
Priority: High
Deadline: Midterm in 12 days

Today:
- Review association rules, 30 min
- Take quiz: Apriori basics, 10 questions

Weak Topics:
- support-confidence: high
- FP-Growth: medium

Documents:
- Lecture 3 PDF
- Assignment 2
```

Project example:

```text
Portfolio RAG Chatbot
Priority: Medium
Deadline: Demo in 3 weeks

Today:
- Implement citation display
- Read notes on vector DB eval

Artifacts:
- GitHub repo link
- Demo checklist
```

Career example:

```text
AI Engineer Internship
Priority: High
Target: Apply by Aug 1

Today:
- Rewrite project bullet in CV
- Review 3 job descriptions

Artifacts:
- CV draft
- portfolio project list
```

### 3.5 Ask document / RAG flow

```text
User opens track
 ↓
Selects Ask Document
 ↓
Types question
 ↓
StudyOps sends query to DeepTutor with track KB context
 ↓
DeepTutor returns answer + citations
 ↓
StudyOps stores KnowledgeQuery summary
 ↓
Optional: Hermes adds mentor guidance
```

Example:

```text
User: "Apriori khác FP-Growth ở đâu?"
DeepTutor: answers based on Lecture 3, citing slides 15-18.
Hermes: "Bạn nên làm thêm quiz về support/confidence vì câu hỏi này liên quan weak topic hiện tại."
```

RAG answers should come from DeepTutor. Hermes may add guidance, but should not invent source-grounded answers when DeepTutor has the KB.

### 3.6 Quiz generation and attempt flow

Generate quiz:

```text
User selects track/topic/document
 ↓
Clicks Generate Quiz
 ↓
StudyOps calls DeepTutor
 ↓
DeepTutor generates quiz
 ↓
StudyOps creates Quiz
 ↓
EventLog(quiz.generated)
```

Attempt quiz:

```text
User answers quiz
 ↓
DeepTutor grades / explains
 ↓
StudyOps creates QuizAttempt
 ↓
StudyOps updates WeakTopic
 ↓
EventLog(quiz.attempt.completed)
 ↓
Trigger weak_topic_remediation job if needed
```

Simple MVP weak topic rule:

```text
score < 50 → severity high
50 <= score < 70 → severity medium
70 <= score < 85 → severity low
```

Hermes may later refine severity, but MVP starts rule-based so behavior is predictable.

### 3.7 Daily coach flow

Daily coach runs at the preferred study time.

```text
AutonomyJob(daily_checkin)
 ↓
StudyOps builds snapshot:
 - active tracks
 - today/tomorrow deadlines
 - open tasks
 - weak topics
 - yesterday completion
 ↓
Hermes generates daily recommendation
 ↓
StudyOps converts recommendation into StudyTask or message
 ↓
Low-risk tasks auto-apply
 ↓
Dashboard shows Today plan
```

Example output:

```text
Hôm nay nên học 75 phút:

1. Data Mining — 35 phút
   Ôn support/confidence vì quiz gần nhất score 55%.

2. RAG Chatbot — 25 phút
   Làm citation display để kịp demo tuần sau.

3. Internship — 15 phút
   Viết lại 1 bullet trong CV theo format impact.
```

Daily coach should be short and actionable, not an essay.

### 3.8 Weekly review / L4 autonomous worker flow

Trigger:

```text
Sunday 20:00 local time
```

Or manually:

```text
Run weekly review now
```

Flow:

```text
1. StudyOps creates AutonomyJob(weekly_review, running).
2. StudyOps builds input_snapshot.
3. Hermes analyzes snapshot.
4. Hermes returns structured output:
   - summary
   - risks
   - track-by-track assessment
   - proposed plan changes
   - proposed new tasks
   - proposed weak-topic remediation
5. StudyOps validates proposal shape.
6. StudyOps risk-classifies each proposed change.
7. Low-risk changes auto-apply.
8. Medium/high-risk changes become ApprovalRequest.
9. User reviews proposals.
10. Approved changes are applied.
11. EventLog records everything.
```

Weekly review input snapshot:

```json
{
  "active_tracks": [],
  "deadlines_next_14_days": [],
  "open_tasks": [],
  "completed_tasks_last_7_days": [],
  "skipped_tasks_last_7_days": [],
  "quiz_attempts_last_14_days": [],
  "weak_topics": [],
  "study_sessions_last_14_days": [],
  "pending_approvals": []
}
```

Weekly review output:

```json
{
  "summary": "Data Mining needs priority this week because midterm is close and quiz score is low.",
  "track_assessments": [
    {
      "track_id": "data-mining",
      "status": "at_risk",
      "reason": "Midterm in 8 days, weak topic support-confidence remains high."
    }
  ],
  "proposals": [
    {
      "proposal_type": "modify_plan",
      "risk_level": "medium",
      "title": "Prioritize Data Mining over project work this week",
      "rationale": "Midterm is closer than project demo.",
      "proposed_changes": {}
    }
  ]
}
```

Hermes does not directly update:

```text
StudyPlan
StudyTask
Track priority
Goal status
Deadline status
```

Hermes proposes; StudyOps applies after policy and approval.

### 3.9 Approval flow

User sees:

```text
Mentor proposal:
"Shift 2 RAG Chatbot tasks to next week and add 3 Data Mining review tasks."

Why:
- Data Mining midterm in 8 days
- Last quiz score: 55%
- RAG demo still has 21 days

Changes:
+ Add task: Review Apriori examples
+ Add task: Quiz support/confidence
- Move task: Implement evaluation dashboard to next week

[Approve] [Reject] [Edit]
```

Approve:

```text
ApprovalRequest(status=approved)
AgentProposal(status=approved)
Apply changes
EventLog(approval.accepted)
```

Reject:

```text
ApprovalRequest(status=rejected)
AgentProposal(status=rejected)
EventLog(approval.rejected)
```

Edit in MVP can be instruction-based:

```text
User: "Keep project task, but reduce internship prep instead."
```

Then StudyOps creates a new `AutonomyJob(plan_rebalance)` with the user instruction.

### 3.10 Failure flows

DeepTutor unavailable:

```text
Show:
"DeepTutor is not available. Check local service at localhost:8001."

Store:
EventLog(service.unavailable)
```

No hallucinated fallback from Hermes for source-grounded Q&A.

9Router unavailable:

```text
Show:
"Model gateway is unavailable. Mentor and tutoring AI features are paused."

Disable:
- mentor chat
- quiz generation
- weekly review
```

Existing dashboard data remains readable.

Hermes unavailable:

```text
Show:
"Mentor agent is unavailable. You can still use documents, quiz, and manual planning."

Disable:
- daily coach generation
- weekly review
- mentor chat
```

Weekly review fails:

```text
AutonomyJob(status=failed, error_message=...)
EventLog(autonomy_job.failed)

Show:
"Weekly review failed. Retry when services are available."
```

Never silently fail.

### 3.11 Notification flow

Phase 1:

```text
In-app notification only
```

Examples:

```text
Daily plan ready
Weekly review needs approval
Quiz remediation tasks added
DeepTutor processing failed
```

Phase 2 optional:

```text
Browser notification
Telegram via Hermes
Discord via Hermes
```

Telegram is not required for MVP because Web UI is primary.

### 3.12 End-to-end MVP scenario

```text
1. User launches StudyOps locally.
2. Configures 9Router.
3. Creates profile:
   "CS student, Year 3, prefers Vietnamese explanations."
4. Creates 3 tracks:
   - Data Mining course
   - RAG Chatbot project
   - AI Internship prep
5. Uploads Data Mining lecture PDF.
6. Asks: "Apriori khác FP-Growth ở đâu?"
7. DeepTutor answers with citations.
8. User generates a 10-question quiz.
9. User scores 55%.
10. StudyOps creates WeakTopic: support-confidence high.
11. Daily Coach creates task:
    "Ôn support/confidence 30 phút ngày mai."
12. Sunday weekly review runs.
13. Hermes proposes:
    - prioritize Data Mining this week
    - delay one project task
    - keep one light internship task
14. User approves.
15. Dashboard updates next-week plan.
```

This demo proves the thesis:

```text
StudyOps connects documents, quiz results, weak topics, deadlines, and autonomous planning into one learning loop.
```

### 3.13 UX priorities for MVP

Must feel clear:

```text
What should I do today?
Why did the mentor suggest this?
What evidence says I am weak here?
What will the agent change if I approve?
```

Avoid early complexity:

```text
No social features
No teacher/admin dashboard
No marketplace
No mobile app
No full OpenClaw integration
No automatic email/submission
No shell command automation
```

### 3.14 Section 3 design decisions

Chốt các quyết định:

1. First-run onboarding must configure model gateway before anything else.
2. User must create at least one track before upload/quiz.
3. Dashboard centers on Today, Tracks, Weak Topics, Approvals.
4. RAG answer comes from DeepTutor; Hermes only adds mentor guidance.
5. Daily coach creates short actionable tasks, not long essays.
6. Weekly review is the primary L4 flow.
7. L4 output becomes proposals, not direct mutations.
8. In-app notification is enough for MVP.
9. If a service is down, StudyOps should degrade gracefully and never fake answers.

---

## Section 4 — Autonomy Design / L4 Worker Policy

The autonomy layer is the safety backbone for L4. StudyOps must distinguish between reasoning and execution:

```text
Hermes = reasoning + proposal generation
StudyOps Core = policy + validation + execution
User = approval authority for risky changes
```

### 4.1 Definition of L4 in StudyOps

In StudyOps, L4 Autonomous Worker means:

```text
The agent can run on schedules/events,
analyze multiple data sources,
plan multi-step actions,
propose or auto-apply low-risk actions,
and report outcomes.
```

It does not mean:

```text
automatic email sending
automatic assignment submission
arbitrary file edits/deletes
shell command execution
external account actions
major roadmap changes without approval
```

Short definition:

> L4 in MVP = autonomous reasoning + controlled execution.

### 4.2 Autonomy architecture

```text
Trigger
  ↓
AutonomyJob
  ↓
Snapshot Builder
  ↓
Hermes Reasoning Worker
  ↓
Structured Proposal Output
  ↓
Policy Engine
  ↓
Validation Layer
  ↓
Execution Layer
  ↓
EventLog + Notification
```

#### Trigger

Triggers create jobs.

```text
scheduled:
- daily_checkin
- weekly_review
- deadline_watch

event-based:
- quiz.attempt.completed
- weak_topic.updated
- study_task.skipped
- knowledge.uploaded

manual:
- user clicks Run weekly review
- user asks Rebalance my week
```

#### `AutonomyJob`

Every agent run must have an `AutonomyJob` record. No background agent should run invisibly.

#### Snapshot Builder

StudyOps Core gathers readonly data for the agent.

Example weekly snapshot:

```json
{
  "user_profile": {},
  "learning_preferences": {},
  "active_tracks": [],
  "deadlines_next_14_days": [],
  "active_study_plan": {},
  "open_tasks": [],
  "completed_tasks_last_7_days": [],
  "skipped_tasks_last_7_days": [],
  "quiz_attempts_last_14_days": [],
  "weak_topics": [],
  "knowledge_items_recent": [],
  "pending_approvals": [],
  "autonomy_policy": {}
}
```

Key rule:

```text
Agent does not query the database freely.
Agent only receives bounded snapshots.
```

Reasons:

- easier testing,
- easier reproduction,
- lower privacy/context exposure,
- smaller prompts,
- debuggable via `AutonomyJob.input_snapshot`.

#### Hermes Reasoning Worker

Hermes receives a snapshot and returns structured output, not free-form prose as the primary output.

Expected shape:

```json
{
  "job_summary": "...",
  "observations": [],
  "risks": [],
  "proposals": [],
  "messages": []
}
```

#### Policy Engine

StudyOps Core classifies proposals as:

```text
auto-apply
needs approval
blocked
```

Hermes may suggest a risk level, but StudyOps Core decides the final classification.

#### Validation Layer

Before execution:

- schema must be valid,
- referenced IDs must exist,
- action must not exceed permissions,
- workload must be reasonable,
- duplicate tasks should be avoided,
- completed tasks should not be mutated,
- data deletion is not allowed,
- plan dates must stay within allowed windows.

#### Execution Layer

Only the execution layer mutates database state.

```text
AgentProposal → Policy → Approval/AutoApply → Execution
```

No direct path:

```text
Hermes → DB write
```

### 4.3 Autonomy job types

#### `daily_checkin`

Goal:

```text
Create a short, feasible plan for today based on priority, deadlines, and weak topics.
```

Trigger:

```text
preferred_study_time daily
```

Allowed outputs:

```text
message
create_tasks
suggest_focus
```

Policy:

```text
small tasks within daily target minutes → auto-apply
major reschedule → needs approval
```

#### `weekly_review`

Goal:

```text
Analyze the past week and propose next-week plan changes.
```

Trigger:

```text
Sunday 20:00
manual run
```

Allowed outputs:

```text
track_assessment
create_plan
modify_plan
create_tasks
adjust_priority
mark_goal_at_risk
update_weak_topic
```

Policy:

```text
new small tasks → auto-apply
modify active plan → approval
adjust priority across tracks → approval
mark goal at risk → approval or confirmation
```

#### `deadline_watch`

Goal:

```text
Detect nearby deadlines and increase attention.
```

Allowed outputs:

```text
message
create_tasks
mark_track_at_risk
```

Policy:

```text
reminder/message → auto
small prep tasks → auto
track priority changes → approval
```

#### `weak_topic_remediation`

Goal:

```text
When the user performs poorly on a quiz, create remediation tasks or practice quizzes.
```

Trigger:

```text
quiz.attempt.completed with score < threshold
weak_topic.updated severity=high
```

Allowed outputs:

```text
create_tasks
create_quiz
update_weak_topic
message
```

Policy:

```text
update weak topic from evidence → auto
create practice quiz/task → auto
change plan priority → approval
```

#### `plan_rebalance`

Goal:

```text
Adjust plan after missed tasks, rejected proposals, or new user instruction.
```

Trigger:

```text
multiple skipped tasks
user clicks rebalance
user edits/rejects weekly proposal with instruction
```

Allowed outputs:

```text
modify_plan
reschedule_tasks
create_tasks
drop_tasks
```

Policy:

```text
reschedule within same track/week → maybe auto
drop tasks → approval
shift effort across tracks → approval
```

### 4.4 Risk classification

#### Low-risk actions

May auto-apply if policy allows:

```text
create a small study task
create a practice quiz
update weak topic from quiz evidence
send in-app notification
summarize weekly progress
tag a document/topic
create reminder inside StudyOps
```

Conditions:

```text
no data deletion
no external account action
no major priority change
no excessive daily workload
no mutation of completed records
```

#### Medium-risk actions

Require approval by default:

```text
modify active weekly plan
reschedule multiple tasks
shift time allocation across tracks
mark a goal/track as at-risk
change track priority
create a long study workload
generate weekly plan replacing existing plan
```

#### High-risk actions

Blocked in MVP or require explicit approval in future:

```text
send email/message outside app
submit assignment
delete documents
delete track/plan/history
run shell command
read arbitrary local files
access external accounts
modify GitHub repo
post to social/chat apps
make purchases/API billing changes
```

MVP should not implement high-risk execution. It can only log `blocked_high_risk_action`.

### 4.5 Policy matrix

```text
Action type                  Default
-----------------------------------------------
create_small_task            auto
create_practice_quiz         auto
update_weak_topic_evidence   auto
send_in_app_notification     auto
summarize_progress           auto

modify_active_plan           approval
reschedule_many_tasks        approval
adjust_track_priority        approval
mark_goal_at_risk            approval
replace_weekly_plan          approval
drop_task                    approval

delete_data                  blocked
external_message             blocked
submit_assignment            blocked
shell_command                blocked
external_account_action      blocked
```

MVP policy:

```text
Auto-apply low-risk.
Approval for medium-risk.
Block high-risk.
```

### 4.6 Structured proposal schema

Hermes should return proposals like:

```json
{
  "proposal_type": "create_tasks",
  "risk_level": "low",
  "title": "Add two Apriori practice tasks",
  "summary": "Add short remediation tasks for weak topic support-confidence.",
  "rationale": "The latest Data Mining quiz score was 55%, with mistakes tagged support-confidence.",
  "evidence_event_ids": ["evt_quiz_123", "evt_weak_topic_456"],
  "proposed_changes": {
    "create_tasks": [
      {
        "track_id": "trk_data_mining",
        "title": "Review support vs confidence examples",
        "task_type": "review",
        "scheduled_for": "2026-06-06",
        "estimated_minutes": 25,
        "priority": "high",
        "linked_knowledge_item_ids": ["kn_lecture_3"]
      },
      {
        "track_id": "trk_data_mining",
        "title": "Take 8-question Apriori practice quiz",
        "task_type": "quiz",
        "scheduled_for": "2026-06-07",
        "estimated_minutes": 20,
        "priority": "high"
      }
    ]
  }
}
```

Validation rules:

```text
proposal_type must be allowed for job type
risk_level cannot be lower than StudyOps Core classification
track_id must exist
scheduled_for must be inside allowed planning window
estimated_minutes must be reasonable
evidence_event_ids should exist for evidence-based claims
```

### 4.7 Weekly review output contract

Weekly review is the flagship L4 workflow.

```json
{
  "job_summary": "This week, Data Mining needs priority because midterm is close and quiz scores are low.",
  "observations": [
    {
      "type": "quiz_performance",
      "track_id": "trk_data_mining",
      "message": "Latest quiz score was 55%.",
      "evidence_event_ids": ["evt_quiz_123"]
    }
  ],
  "track_assessments": [
    {
      "track_id": "trk_data_mining",
      "status": "at_risk",
      "confidence": 0.82,
      "reasons": [
        "Midterm in 8 days",
        "Weak topic support-confidence remains high"
      ],
      "evidence_event_ids": ["evt_deadline_1", "evt_weak_topic_456"]
    }
  ],
  "proposals": [
    {
      "proposal_type": "modify_plan",
      "risk_level": "medium",
      "title": "Prioritize Data Mining this week",
      "summary": "Move two project tasks to next week and add three Data Mining review tasks.",
      "rationale": "Data Mining midterm is closer and recent quiz performance is weak.",
      "evidence_event_ids": ["evt_deadline_1", "evt_quiz_123"],
      "proposed_changes": {}
    }
  ],
  "user_message": "Tuần này nên ưu tiên Data Mining vì midterm đang gần và bạn còn yếu support/confidence."
}
```

### 4.8 Snapshot design

Daily snapshot:

```json
{
  "date": "2026-06-05",
  "available_minutes": 75,
  "active_tracks": [],
  "deadlines_next_3_days": [],
  "open_tasks": [],
  "weak_topics": [],
  "recent_quiz_attempts": [],
  "yesterday_summary": {}
}
```

Weekly snapshot:

```json
{
  "week_start": "2026-06-01",
  "week_end": "2026-06-07",
  "active_tracks": [],
  "deadlines_next_30_days": [],
  "task_stats": {
    "completed": 8,
    "skipped": 4,
    "overdue": 2
  },
  "track_summaries": [],
  "quiz_attempts_last_14_days": [],
  "weak_topics": [],
  "pending_approvals": [],
  "policy": {}
}
```

Weak-topic remediation snapshot:

```json
{
  "quiz_attempt": {},
  "weak_topics": [],
  "related_knowledge_items": [],
  "upcoming_deadlines": [],
  "current_plan_tasks": []
}
```

### 4.9 Autonomy loop control

MVP must prevent runaway behavior.

Controls:

```text
max_jobs_per_day
max_proposals_per_job
max_auto_tasks_per_day
max_auto_quizzes_per_day
max_llm_calls_per_job
job_timeout_seconds
cooldown per trigger type
```

Suggested defaults:

```text
max_jobs_per_day = 10
max_proposals_per_job = 5
max_auto_tasks_per_day = 5
max_auto_quizzes_per_day = 3
max_llm_calls_per_job = 3 for daily, 8 for weekly
job_timeout_seconds = 180
cooldown weak_topic_remediation = 12h per topic
```

Important rule:

```text
No recursive autonomy in MVP.
```

An `AutonomyJob` can create proposals/tasks, but cannot directly trigger another `AutonomyJob` immediately except through explicitly allowed event triggers with cooldown.

### 4.10 Evidence and explainability

Every user-facing agent decision should answer:

```text
What changed?
Why?
Based on what evidence?
What can I approve/reject?
```

Proposal UI should include:

```text
title
summary
rationale
evidence list
proposed changes
risk level
buttons/actions
```

Example:

```text
Proposal: Prioritize Data Mining this week

Why:
- Midterm in 8 days
- Last quiz score: 55%
- Weak topic: support-confidence high

Changes:
- Add 3 Data Mining tasks
- Move 1 RAG task to next week

Risk: Medium
Needs approval because it shifts time across tracks.
```

### 4.11 Human override

User must always be able to:

```text
pause autonomy
disable a job type
reject proposal
edit proposal instruction
delete/disable a track
mark weak topic ignored
set track priority manually
set quiet hours
```

Manual user choice overrides agent suggestion. If user rejects the same proposal type repeatedly, StudyOps should reduce future suggestions of that type.

### 4.12 Failure and recovery policy

Hermes returns invalid schema:

```text
AutonomyJob(status=failed)
EventLog(autonomy_job.invalid_output)
Show retry option
No state mutation
```

Hermes proposes impossible action:

```text
reject proposal
store validation error
do not execute
```

Policy blocks action:

```text
AgentProposal(status=rejected or blocked)
EventLog(agent_proposal.blocked_by_policy)
Show user if relevant
```

LLM call fails:

```text
AutonomyJob(status=failed)
error_message saved
retry later
```

Never silently fail.

### 4.13 OpenClaw future integration

OpenClaw should not be in the MVP execution path.

Future role:

```text
OpenClaw = local assistant shell / device control plane
StudyOps Core = product state
Hermes or OpenClaw agent = autonomy worker
DeepTutor = education engine
```

Possible future integrations:

```text
desktop notifications
voice check-in
screen/context capture
local file awareness
calendar integration
Google Workspace tools
```

But StudyOps policy remains:

```text
OpenClaw cannot bypass StudyOps Core policy.
Any external/device action still goes through ApprovalRequest.
```

### 4.14 Minimal L4 MVP boundary

MVP includes:

```text
daily_checkin
weekly_review
weak_topic_remediation
deadline_watch
manual plan_rebalance
```

Explicitly excluded:

```text
email sending
assignment submission
calendar write
local file operations beyond uploaded files
shell command execution
GitHub modification
automatic external messaging
```

This is still L4 because the worker:

```text
runs independently,
uses multi-source context,
plans across tracks,
creates proposals,
auto-applies safe actions,
and reports outcomes.
```

### 4.15 Section 4 design decisions

Chốt các quyết định:

1. L4 = autonomous reasoning + controlled execution.
2. All autonomy runs as `AutonomyJob`.
3. Agent receives snapshots, not raw DB access.
4. Hermes returns structured output only.
5. StudyOps Core owns risk classification and execution.
6. Low-risk actions can auto-apply.
7. Medium-risk actions require approval.
8. High-risk actions are blocked in MVP.
9. Weekly review is the flagship L4 workflow.
10. Loop limits are mandatory.
11. Every proposal must be explainable with evidence.
12. OpenClaw is future integration, not MVP dependency.

---

## Section 5 — Service Integration Contracts

This section defines how services talk to each other. Because the project uses glue-only integration, StudyOps Core is the bridge and source of truth.

```text
Web UI
 ↓
StudyOps Core
 ├── DeepTutor Adapter
 ├── Hermes Adapter
 ├── 9Router Config / Health Check
 └── Local DB / EventLog
```

Rule:

```text
Frontend should not call DeepTutor/Hermes directly for product-state-changing actions.
Frontend calls StudyOps Core.
StudyOps Core calls external services.
StudyOps Core writes EventLog.
```

### 5.1 Integration principles

#### Principle 1 — StudyOps Core owns product state

DeepTutor may have KB/document IDs. Hermes may have memory/session IDs. Product state lives in StudyOps:

```text
Track
Goal
Deadline
KnowledgeItem
Quiz
QuizAttempt
WeakTopic
StudyPlan
StudyTask
AutonomyJob
AgentProposal
ApprovalRequest
EventLog
```

External service IDs are references only.

#### Principle 2 — Adapters isolate upstream changes

Use adapter layer:

```text
studyops_core/adapters/deeptutor.py
studyops_core/adapters/hermes.py
studyops_core/adapters/router.py
```

If an upstream API changes, only the adapter should change.

#### Principle 3 — Contract-first internal API

Define ideal internal APIs first:

```text
DeepTutorAdapter.create_kb(...)
DeepTutorAdapter.ask_document(...)
DeepTutorAdapter.generate_quiz(...)
DeepTutorAdapter.grade_quiz(...)

HermesAdapter.run_daily_checkin(...)
HermesAdapter.run_weekly_review(...)
HermesAdapter.run_plan_rebalance(...)
```

Adapter implementation can use:

```text
HTTP API
CLI wrapper
local script call
temporary mock
```

#### Principle 4 — No silent fallback for source-grounded answers

If DeepTutor fails, Hermes must not pretend to answer from uploaded documents.

Policy:

```text
DeepTutor unavailable → show service error.
Hermes may say: “I can explain generally, but not from your uploaded document.”
```

#### Principle 5 — All integration actions produce events

Examples:

```text
deeptutor.kb.created
deeptutor.document.processing_failed
hermes.weekly_review.completed
router.health_check.failed
```

### 5.2 Service topology

MVP local Docker Compose:

```text
studyops-core        http://localhost:8000
deeptutor-backend    http://localhost:8001
deeptutor-frontend   http://localhost:3782
hermes-agent         http://localhost:9000 or CLI daemon
9router              http://localhost:20128/v1
sqlite               local file volume
uploaded-files       local file volume
```

Data ownership:

```text
StudyOps Core:
- product state
- tracks/plans/tasks
- event log
- autonomy policy
- proposal/approval state

DeepTutor:
- document parsing
- KB/vector index
- RAG answers
- tutoring/quiz generation internals

Hermes:
- agent reasoning
- mentor dialogue
- scheduled/long-running worker behavior
- skill/tool usage

9Router:
- LLM provider routing
- OpenAI-compatible API
- fallback/cost/token gateway
```

### 5.3 StudyOps Core public API

Used by frontend.

#### Health

```http
GET /health
GET /health/services
```

Response:

```json
{
  "studyops_core": "ok",
  "deeptutor": "ok",
  "hermes": "ok",
  "router": "ok"
}
```

#### Profile / settings

```http
GET /profile
PUT /profile
GET /preferences
PUT /preferences
GET /settings
PUT /settings
POST /settings/test-model-gateway
```

#### Tracks

```http
GET /tracks
POST /tracks
GET /tracks/{track_id}
PATCH /tracks/{track_id}
POST /tracks/{track_id}/pause
POST /tracks/{track_id}/archive
```

`PATCH /tracks/{track_id}` is for direct user actions. Hermes proposes changes through `AgentProposal`.

#### Goals / deadlines

```http
GET /tracks/{track_id}/goals
POST /tracks/{track_id}/goals
PATCH /goals/{goal_id}

GET /tracks/{track_id}/deadlines
POST /tracks/{track_id}/deadlines
PATCH /deadlines/{deadline_id}
```

#### Knowledge

```http
GET /tracks/{track_id}/knowledge
POST /tracks/{track_id}/knowledge/upload
GET /knowledge/{knowledge_item_id}
POST /knowledge/{knowledge_item_id}/ask
```

Ask request:

```json
{
  "question": "Apriori khác FP-Growth ở đâu?",
  "language": "vi",
  "include_mentor_guidance": true
}
```

Ask response:

```json
{
  "answer": "...",
  "citations": [
    {
      "source": "Lecture 3",
      "page": 12,
      "snippet": "..."
    }
  ],
  "mentor_guidance": "Bạn nên làm thêm quiz về support/confidence.",
  "knowledge_query_id": "kq_123"
}
```

#### Quiz

```http
POST /tracks/{track_id}/quizzes/generate
GET /tracks/{track_id}/quizzes
GET /quizzes/{quiz_id}
POST /quizzes/{quiz_id}/attempts
GET /quizzes/{quiz_id}/attempts
```

Generate request:

```json
{
  "knowledge_item_ids": ["kn_1"],
  "topic_tags": ["apriori", "association-rules"],
  "difficulty": "medium",
  "question_count": 10,
  "language": "vi"
}
```

Attempt response:

```json
{
  "attempt_id": "qa_123",
  "score": 55,
  "correct_count": 6,
  "total_count": 11,
  "mistake_topic_tags": ["support-confidence"],
  "feedback_summary": "User confused support and confidence.",
  "weak_topics_updated": ["wt_1"]
}
```

#### Plans / tasks

```http
GET /plans/current
POST /plans
GET /tracks/{track_id}/tasks
POST /tasks
PATCH /tasks/{task_id}
POST /tasks/{task_id}/complete
POST /tasks/{task_id}/skip
```

Manual task creation is direct. Agent-created tasks go through `AgentProposal` unless policy allows auto-apply.

#### Autonomy

```http
GET /autonomy/policy
PUT /autonomy/policy

GET /autonomy/jobs
POST /autonomy/jobs/run
GET /autonomy/jobs/{job_id}

GET /proposals
GET /proposals/{proposal_id}
POST /proposals/{proposal_id}/approve
POST /proposals/{proposal_id}/reject
POST /proposals/{proposal_id}/edit
```

Run job request:

```json
{
  "job_type": "weekly_review",
  "reason": "manual_run"
}
```

#### Events

```http
GET /events
GET /tracks/{track_id}/events
```

Useful for debugging, even if internal in MVP.

### 5.4 DeepTutor Adapter contract

StudyOps Core talks to DeepTutor through an adapter.

#### `create_or_get_kb(track)`

Input:

```json
{
  "track_id": "trk_data_mining",
  "title": "Data Mining",
  "description": "Course track"
}
```

Output:

```json
{
  "deeptutor_kb_id": "dt_kb_123"
}
```

#### `upload_document(track_id, file)`

Input:

```json
{
  "track_id": "trk_data_mining",
  "deeptutor_kb_id": "dt_kb_123",
  "file_path": "/local/uploads/lecture3.pdf",
  "title": "Lecture 3 Association Rules"
}
```

Output:

```json
{
  "deeptutor_document_id": "dt_doc_456",
  "status": "processing"
}
```

MVP can poll for processing status.

#### `get_document_status(document_id)`

Output:

```json
{
  "status": "ready",
  "error_message": null
}
```

#### `ask_document(...)`

Input:

```json
{
  "deeptutor_kb_id": "dt_kb_123",
  "question": "Apriori khác FP-Growth ở đâu?",
  "language": "vi",
  "citation_required": true
}
```

Output:

```json
{
  "answer": "...",
  "citations": [
    {
      "document_id": "dt_doc_456",
      "title": "Lecture 3",
      "page": 12,
      "snippet": "..."
    }
  ],
  "session_id": "dt_session_789"
}
```

#### `generate_quiz(...)`

Input:

```json
{
  "deeptutor_kb_id": "dt_kb_123",
  "document_ids": ["dt_doc_456"],
  "topic_tags": ["apriori", "association-rules"],
  "difficulty": "medium",
  "question_count": 10,
  "language": "vi",
  "explanation_style": "step_by_step"
}
```

Output:

```json
{
  "deeptutor_quiz_id": "dt_quiz_111",
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice",
      "question": "...",
      "choices": [],
      "topic_tags": ["support-confidence"]
    }
  ]
}
```

#### `grade_quiz(...)`

Input:

```json
{
  "deeptutor_quiz_id": "dt_quiz_111",
  "answers": [
    {
      "question_id": "q1",
      "answer": "B"
    }
  ]
}
```

Output:

```json
{
  "deeptutor_attempt_id": "dt_attempt_222",
  "score": 55,
  "correct_count": 6,
  "total_count": 11,
  "question_results": [],
  "mistake_topic_tags": ["support-confidence"],
  "feedback_summary": "User confused support and confidence."
}
```

### 5.5 Hermes Adapter contract

StudyOps Core invokes Hermes for reasoning.

Rules:

```text
Hermes receives snapshots.
Hermes returns structured outputs.
Hermes does not mutate StudyOps DB.
```

#### `run_daily_checkin(snapshot)`

Input:

```json
{
  "job_id": "job_123",
  "job_type": "daily_checkin",
  "snapshot": {
    "date": "2026-06-05",
    "available_minutes": 75,
    "active_tracks": [],
    "deadlines_next_3_days": [],
    "open_tasks": [],
    "weak_topics": [],
    "policy": {}
  }
}
```

Output:

```json
{
  "job_summary": "Today should focus on Data Mining and a small project task.",
  "messages": [
    {
      "channel": "in_app",
      "text": "Hôm nay nên học 75 phút..."
    }
  ],
  "proposals": [
    {
      "proposal_type": "create_tasks",
      "risk_level": "low",
      "title": "Create today's study tasks",
      "summary": "...",
      "rationale": "...",
      "evidence_event_ids": [],
      "proposed_changes": {}
    }
  ]
}
```

#### `run_weekly_review(snapshot)`

Input:

```json
{
  "job_id": "job_456",
  "job_type": "weekly_review",
  "snapshot": {
    "week_start": "2026-06-01",
    "week_end": "2026-06-07",
    "active_tracks": [],
    "deadlines_next_30_days": [],
    "task_stats": {},
    "quiz_attempts_last_14_days": [],
    "weak_topics": [],
    "policy": {}
  }
}
```

Output follows the Section 4 weekly review schema.

#### `run_plan_rebalance(snapshot, instruction)`

Input:

```json
{
  "job_id": "job_789",
  "job_type": "plan_rebalance",
  "instruction": "Keep project task, but reduce internship prep instead.",
  "snapshot": {}
}
```

Output:

```json
{
  "job_summary": "...",
  "proposals": []
}
```

#### `mentor_chat(message, context)`

Optional for MVP.

Input:

```json
{
  "message": "Tối nay học gì?",
  "context": {
    "profile": {},
    "today_tasks": [],
    "active_tracks": [],
    "weak_topics": [],
    "deadlines": []
  }
}
```

Output:

```json
{
  "reply": "Tối nay bạn nên ưu tiên Data Mining...",
  "suggested_actions": []
}
```

`mentor_chat` can suggest actions, but state-changing actions still become proposals.

### 5.6 9Router integration contract

9Router is treated as an OpenAI-compatible LLM endpoint.

Config:

```text
base_url = http://localhost:20128/v1
api_key = user-provided
default_chat_model
default_reasoning_model
default_embedding_model
```

Health check options:

```http
GET /v1/models
```

or a minimal chat completion:

```text
"Reply with OK"
```

StudyOps stores:

```text
router reachable?
available models?
last health check time
```

StudyOps Core does not need to proxy every model call in MVP. It can configure DeepTutor/Hermes to use 9Router directly, while still testing and displaying health.

### 5.7 UI integration strategy

Because the primary UI uses DeepTutor frontend surface, there are two MVP paths.

#### Path A — Launcher dashboard first

Build a small StudyOps Web Shell at `localhost:8000/ui`:

```text
Dashboard
Tracks
Approvals
Settings
Links into DeepTutor UI
```

DeepTutor frontend remains at `localhost:3782`.

Pros:

```text
fastest
no fork DeepTutor frontend
clean glue-only
```

Cons:

```text
two web surfaces
less integrated UX
```

#### Path B — Embed StudyOps panels into DeepTutor frontend

Light fork or plugin-style modification:

```text
DeepTutor UI + StudyOps sidebar/panel
```

Pros:

```text
more unified UX
```

Cons:

```text
requires modifying/forking DeepTutor frontend
upstream maintenance risk
```

Recommendation for MVP:

```text
Start with Path A.
After the backend/product loop works, move toward Path B.
```

### 5.8 Error contract

Every adapter call should return a normalized error:

```json
{
  "ok": false,
  "service": "deeptutor",
  "operation": "generate_quiz",
  "error_type": "service_unavailable",
  "message": "DeepTutor is not reachable at localhost:8001.",
  "retryable": true
}
```

Error types:

```text
service_unavailable
timeout
invalid_response
auth_failed
rate_limited
model_error
processing_failed
unsupported_operation
```

StudyOps should write:

```text
EventLog(service.operation_failed)
```

User-facing errors should include a short message and a clear next step, not stack traces by default.

### 5.9 Contract testing

Define contract tests early.

DeepTutor adapter:

```text
create KB
upload doc
poll status
ask doc
generate quiz
grade quiz
```

Hermes adapter:

```text
daily checkin returns valid schema
weekly review returns valid schema
invalid output is rejected
plan rebalance respects instruction
```

9Router:

```text
health check
chat completion
model list or fallback test
```

Mock adapters should exist for development:

```text
MockDeepTutorAdapter
MockHermesAdapter
MockRouterAdapter
```

This lets StudyOps Core and UI be built before all external services are fully wired.

### 5.10 Section 5 design decisions

Chốt các quyết định:

1. Frontend calls StudyOps Core for product actions.
2. StudyOps Core owns all product state.
3. DeepTutor/Hermes/9Router are accessed through adapters.
4. DeepTutor handles source-grounded tutoring/RAG/quiz.
5. Hermes handles reasoning and mentor/autonomy outputs.
6. 9Router is configured as OpenAI-compatible endpoint.
7. StudyOps stores external IDs only as references.
8. No silent fallback when DeepTutor is unavailable.
9. Start MVP UI with StudyOps Web Shell + links to DeepTutor UI; integrate deeper later.
10. Adapter contract tests are mandatory early.

---

## Section 6 — MVP Phases and Testing Strategy

This section turns the design into an 8-12 week roadmap. The implementation philosophy is:

```text
Build the learning loop before polishing the product.
```

Minimal learning loop:

```text
Track → Document → Quiz → WeakTopic → Daily task → Weekly review → Proposal → Approval → Updated plan
```

If this loop works, StudyOps has a clear product thesis.

### 6.1 MVP success criteria

MVP succeeds if one local user can:

```text
1. Run the local stack through Docker Compose / setup script.
2. Configure 9Router and pass model health check.
3. Create a learning profile.
4. Create at least three tracks:
   - course
   - project
   - career
5. Upload a document into a course track.
6. Ask that document and receive an answer with citations.
7. Generate a quiz from the document.
8. Complete the quiz and receive score + feedback.
9. StudyOps creates/updates WeakTopic based on quiz results.
10. Daily Coach creates a short study task.
11. Weekly Review L4 runs and creates a multi-track proposal.
12. User approves the proposal.
13. StudyOps updates StudyPlan/StudyTask.
14. EventLog records the whole chain.
```

The demo should prove:

```text
StudyOps does not just answer questions.
StudyOps closes the learning loop using real learning data.
```

### 6.2 Phased roadmap overview

8-12 week roadmap:

```text
Phase 0 — Repo/bootstrap decisions
Phase 1 — StudyOps Core skeleton + DB
Phase 2 — Web Shell + onboarding + tracks
Phase 3 — DeepTutor adapter + knowledge/quiz loop
Phase 4 — Weak topic + planning loop
Phase 5 — Hermes adapter + daily coach
Phase 6 — L4 weekly review + approvals
Phase 7 — Integration hardening + demo polish
```

Suggested timing:

```text
Weeks 1-2: Core + data model
Weeks 3-4: UI + tracks + knowledge
Weeks 5-6: quiz + weak topics + plans
Weeks 7-8: Hermes + daily coach
Weeks 9-10: L4 weekly review + approval
Weeks 11-12: hardening, testing, docs, demo
```

### 6.3 Phase 0 — Repo / bootstrap decisions

Goal: prepare project structure without building major features.

Deliverables:

```text
docker-compose.yml draft
.env.example
README setup draft
StudyOps Core app skeleton
adapter interfaces
local data directories
```

Recommended stack:

```text
Backend: FastAPI
DB: SQLite
ORM: SQLModel or SQLAlchemy
Migration: Alembic, or simple SQLModel create_all for early MVP
Frontend: simple React/Vite or FastAPI-served minimal web shell
Adapters: Python classes
Background jobs: APScheduler or simple worker loop
```

Recommended local-first choice:

```text
FastAPI + SQLite + SQLModel + simple React/Vite Web Shell
```

Phase tests:

```text
App boots
/health returns ok
SQLite file created
.env loaded
```

### 6.4 Phase 1 — StudyOps Core skeleton + DB

Goal: build the source of truth before AI integrations.

Build entities:

```text
UserProfile
LearningPreference
Track
Goal
Deadline
KnowledgeItem
Quiz
QuizAttempt
WeakTopic
StudyPlan
StudyTask
EventLog
AutonomyJob
AgentProposal
ApprovalRequest
AutonomyPolicy
UserSettings
```

Build API:

```text
GET /health
GET/PUT /profile
GET/PUT /preferences
GET/PUT /settings
GET/POST /tracks
GET/PATCH /tracks/{id}
GET/POST /tracks/{id}/goals
GET/POST /tracks/{id}/deadlines
GET /events
```

Build event writer:

```text
write_event(event_type, actor, payload, track_id?)
```

Acceptance criteria:

```text
Can create profile
Can create 3 tracks
Can add goals/deadlines
Events are written
Can query events by track
```

Tests:

```text
create profile
create track
create goal
create deadline
event log write
invalid track rejected
POST /tracks returns track
GET /tracks lists created tracks
GET /tracks/{id}/events returns event history
```

### 6.5 Phase 2 — Web Shell + onboarding + tracks

Goal: user can set up StudyOps from browser.

Build pages:

```text
Setup wizard
Dashboard
Tracks list
Track detail
Settings
Events/debug page
```

Onboarding:

```text
model gateway config
profile
learning preferences
create first tracks
create goals/deadlines
autonomy policy preset
```

Dashboard v0:

```text
Today placeholder
Tracks list
Deadlines
Approvals placeholder
Service health
```

Acceptance criteria:

```text
Fresh user can complete onboarding
Can create Data Mining / RAG Project / Internship tracks
Can see tracks on dashboard
Can edit profile/settings
```

Tests:

```text
first-run wizard happy path
track creation validation
settings saved
refresh page keeps state
settings update
autonomy policy created
```

### 6.6 Phase 3 — DeepTutor adapter + knowledge/quiz loop

Goal: connect DeepTutor enough to upload documents, ask documents, and generate quizzes.

Adapter interface:

```python
class DeepTutorAdapter:
    create_or_get_kb(track) -> KbRef
    upload_document(track_id, file_path, title) -> DocumentRef
    get_document_status(document_id) -> DocumentStatus
    ask_document(kb_id, question, language) -> RagAnswer
    generate_quiz(...) -> QuizPayload
    grade_quiz(...) -> QuizResult
```

StudyOps APIs:

```text
POST /tracks/{track_id}/knowledge/upload
GET /tracks/{track_id}/knowledge
POST /knowledge/{knowledge_item_id}/ask
POST /tracks/{track_id}/quizzes/generate
POST /quizzes/{quiz_id}/attempts
```

Development fallback:

```text
MockDeepTutorAdapter
```

Acceptance criteria:

```text
Upload a PDF to Data Mining track
KnowledgeItem status becomes ready
Ask a question and get answer + citations
Generate quiz
Submit answers
Receive score/feedback
QuizAttempt saved
Events written
```

Tests:

```text
DeepTutor adapter mock returns expected schema
invalid DeepTutor response is normalized error
upload failure creates KnowledgeItem failed
ask failure does not call Hermes fallback
upload → ask → quiz → attempt
```

### 6.7 Phase 4 — Weak topic + planning loop

Goal: turn quiz results into directed learning.

Weak topic rules:

```text
score < 50 → high
50 <= score < 70 → medium
70 <= score < 85 → low
```

MVP topic extraction:

```text
use DeepTutor mistake_topic_tags if available
else map question topic_tags from incorrect answers
```

Planning APIs:

```text
GET /plans/current
POST /plans
GET /tracks/{track_id}/tasks
POST /tasks
PATCH /tasks/{task_id}
POST /tasks/{task_id}/complete
POST /tasks/{task_id}/skip
```

Auto-remediation v0:

```text
If quiz score < 70:
  create StudyTask:
    "Review weak topic: X"
```

This can start rule-based before Hermes.

Acceptance criteria:

```text
QuizAttempt below threshold creates/updates WeakTopic
WeakTopic has evidence event IDs
Remediation task is created
Task appears on dashboard
User can mark task done/skipped
```

Tests:

```text
score 45 creates high severity
score 60 creates medium severity
score 80 creates low severity
existing WeakTopic updates instead of duplicate
evidence_event_ids recorded
complete task writes event
skip task writes event
```

### 6.8 Phase 5 — Hermes adapter + daily coach

Goal: bring in mentor reasoning without full weekly L4 yet.

Hermes adapter:

```python
class HermesAdapter:
    run_daily_checkin(snapshot) -> AgentRunOutput
    run_weekly_review(snapshot) -> AgentRunOutput
    run_plan_rebalance(snapshot, instruction) -> AgentRunOutput
    mentor_chat(message, context) -> MentorReply
```

Daily snapshot builder:

```text
active tracks
today/tomorrow deadlines
open tasks
weak topics
yesterday completion
learning preferences
autonomy policy
```

Daily checkin flow:

```text
AutonomyJob(daily_checkin)
snapshot
Hermes output
validate proposals
auto-apply low-risk create_tasks
write events
show Today plan
```

Acceptance criteria:

```text
Run daily_checkin manually
Hermes returns valid structured output
Low-risk tasks are auto-created
Invalid Hermes output is rejected
Job status changes succeeded/failed correctly
```

Tests:

```text
Hermes daily output validates
invalid proposal_type rejected
task references nonexistent track rejected
estimated_minutes too high rejected
daily checkin creates <= max_auto_tasks_per_day
no recursive jobs triggered
```

### 6.9 Phase 6 — L4 weekly review + approvals

Goal: ship the flagship L4 workflow.

Weekly snapshot builder:

```text
active tracks
deadlines next 30 days
task stats
quiz attempts last 14 days
weak topics
pending approvals
autonomy policy
```

Weekly review job:

```text
create AutonomyJob
build snapshot
call Hermes
validate structured output
create AgentProposal records
risk classify
auto-apply low-risk
create ApprovalRequest for medium-risk
block high-risk
```

Approval UI:

```text
proposal detail
why/evidence
proposed changes
approve/reject/edit
```

Execution layer supports limited mutations first:

```text
create_tasks
reschedule_tasks
update_weak_topic
mark_goal_at_risk
```

Defer complex mutations:

```text
full plan replacement
priority rewrite across all tracks
```

Acceptance criteria:

```text
Weekly review runs manually
Produces track assessment
Creates at least one proposal
Medium-risk proposal requires approval
Approve applies changes
Reject does not apply changes
EventLog records all steps
Blocked high-risk action does not execute
```

Tests:

```text
policy classification low/medium/high
approval required for modify_plan
high-risk action blocked
invalid proposed_changes rejected
seed user with tracks/tasks/quiz results
run weekly review with mock Hermes
approve proposal
verify tasks changed
verify events written
```

Golden demo:

```text
Data Mining weak + midterm close
RAG project less urgent
Internship light task
Weekly review proposes rebalancing
User approves
Dashboard updates
```

### 6.10 Phase 7 — Integration hardening + demo polish

Goal: make the system reliable enough to demo and self-host.

Hardening:

```text
service health page
adapter error normalization
retry buttons
logs/events viewer
data backup/export
setup docs
.env validation
Docker Compose polish
```

Demo polish:

```text
sample seed data
sample PDF
guided demo script
clear empty states
good error messages
```

UX polish:

```text
Today dashboard
Track status badges
Weak topic evidence view
Approval diff view
Job status view
```

Acceptance criteria:

```text
Fresh clone → setup → run demo in <30 minutes
Services down show understandable errors
No silent autonomy failures
User can inspect why proposal was made
```

### 6.11 Testing strategy overview

#### Unit tests

Target:

```text
data model rules
weak topic rules
policy engine
proposal validation
snapshot builders
event writer
```

Examples:

```text
WeakTopic requires track_id
AgentProposal requires rationale
Medium-risk proposal creates ApprovalRequest
High-risk proposal blocked
```

#### API tests

Target:

```text
profile/tracks/goals/deadlines
knowledge upload lifecycle
quiz attempt lifecycle
task lifecycle
autonomy job lifecycle
approval lifecycle
```

#### Adapter contract tests

Each adapter should have:

```text
mock contract tests
real-service smoke tests
invalid-response tests
timeout tests
```

#### Integration tests

Critical loops:

```text
onboarding → create tracks
upload doc → ask doc
generate quiz → attempt → weak topic
daily checkin → task auto-created
weekly review → proposal → approval → plan updated
service down → graceful error
```

#### Agent output validation tests

Because Hermes output is LLM-generated, every output path must be schema-validated.

Test cases:

```text
missing proposal_type
invalid risk_level
nonexistent track_id
too many tasks
estimated_minutes too high
action not allowed for job type
high-risk action proposed
no evidence for evidence-based claim
```

#### Golden scenario tests

Seed:

```text
User: CS student
Tracks:
- Data Mining, midterm in 8 days
- RAG Chatbot, demo in 21 days
- AI Internship, target in 60 days

Quiz:
- Data Mining score 55
- weak topic support-confidence high

Tasks:
- some completed
- some skipped
```

Expected:

```text
Weekly review marks Data Mining at risk.
Creates proposal to add Data Mining tasks.
Moves one RAG task later.
Keeps one internship light task.
Requires approval.
After approval, tasks update.
```

### 6.12 Manual QA checklist

Before calling MVP done:

```text
Can start local stack
Can configure 9Router
Can create profile/tracks/goals/deadlines
Can upload document
Can ask document with citation
Can generate and attempt quiz
Weak topics update correctly
Daily coach creates reasonable tasks
Weekly review creates explainable proposal
Approval applies changes
Reject does not apply changes
Service failures are visible
EventLog shows audit trail
```

### 6.13 Risks and mitigations

#### Risk 1 — DeepTutor API mismatch

Mitigation:

```text
Use adapter abstraction.
Start with MockDeepTutorAdapter.
Investigate actual DeepTutor API before Phase 3.
If needed, wrap DeepTutor CLI/internal API locally.
```

#### Risk 2 — Hermes structured output instability

Mitigation:

```text
Strict JSON schema validation.
Retry once with validation error.
Reject invalid output.
Use mock Hermes for deterministic tests.
Keep proposal schema simple.
```

#### Risk 3 — L4 feels unsafe or noisy

Mitigation:

```text
max_auto_tasks_per_day
max_proposals_per_job
cooldowns
approval for medium-risk
clear pause autonomy button
```

#### Risk 4 — Multi-track complexity overwhelms user

Mitigation:

```text
Today-first dashboard.
Only show top 3 tasks.
Collapse secondary tracks.
Use risk badges.
```

#### Risk 5 — Local setup too hard

Mitigation:

```text
Docker Compose.
.env.example.
Health page.
Mock mode.
Setup script.
Clear logs.
```

### 6.14 Recommended build order

Do not start with Hermes or OpenClaw.

Recommended order:

```text
1. StudyOps Core DB + API
2. Web Shell onboarding
3. DeepTutor knowledge + quiz loop
4. Weak topic + task planning loop
5. Hermes daily coach
6. Hermes weekly review
7. Approval + execution
8. Hardening
```

Reasons:

```text
Without product state, agent output has nowhere safe to land.
Without quiz/weak topics, weekly review has no evidence.
Without approval, L4 is unsafe.
```

### 6.15 Explicit non-goals for MVP

Do not build:

```text
teacher/admin dashboard
multi-user cloud auth
mobile app
social/community features
payment/billing
teacher grading integration
automatic email
calendar write access
shell command execution
OpenClaw device automation
full DeepTutor frontend fork
full Hermes skill marketplace integration
```

### 6.16 Final MVP definition

MVP is:

```text
A local-first StudyOps Web Shell + Core backend
that connects to DeepTutor, Hermes, and 9Router
to help a university student manage multiple study/career tracks,
learn from uploaded documents,
generate quizzes,
track weak topics,
receive daily coaching,
and run a controlled L4 weekly review
that proposes plan changes with evidence and approval.
```

MVP is not:

```text
an all-purpose AI assistant
a full LMS
a teacher platform
a code automation agent
a merged fork of 3 repos
```

### 6.17 Section 6 design decisions

Chốt các quyết định:

1. Roadmap 8-12 weeks across 7 phases.
2. StudyOps Core and DB come first.
3. DeepTutor integration before Hermes weekly autonomy.
4. Weak-topic evidence loop is required before L4 feels meaningful.
5. Weekly review is the flagship L4 demo.
6. Mock adapters are mandatory to reduce integration risk.
7. High-risk actions stay out of MVP.
8. MVP success is the complete learning loop, not UI polish.

---

## Final Summary / Product Spec

### Product

**StudyOps Mentor** is a local-first personal study operating system for university students managing multiple courses, projects, and career/internship goals.

### Target user

A university student who needs one mentor-like system to coordinate:

```text
course learning
project execution
internship/career preparation
deadlines
uploaded learning materials
weak topics
weekly planning
```

### Core architecture

```text
StudyOps Core = control plane and source of truth
DeepTutor = education engine for RAG, tutoring, quiz, document Q&A
Hermes Agent = mentor reasoning, daily coach, L4 weekly review
9Router = OpenAI-compatible LLM/model gateway
OpenClaw = future local assistant/device-control layer, not MVP dependency
```

### Deployment

```text
Local-first self-hosted stack
Docker Compose preferred
SQLite for StudyOps state
DeepTutor owns vector/RAG internals
9Router provides model gateway
```

### MVP loop

```text
Create tracks
Upload documents
Ask document with citation
Generate quiz
Complete quiz
Update weak topics
Create daily study tasks
Run L4 weekly review
Show evidence-backed proposal
User approves
Plan updates
EventLog records everything
```

### Key product principles

```text
One product, many services
Tracks are first-class
Autonomy with receipts
Proposal before mutation
Low-risk auto, medium-risk approval, high-risk blocked
No silent fallback for source-grounded answers
```

### MVP scope

Must-have:

```text
Knowledge Workspace
Quiz + Weak Topic Tracking
Mentor Memory + Daily Coach
Multi-track support
Controlled L4 Weekly Review
Approval workflow
EventLog audit trail
Service health and graceful failure handling
```

Explicit non-goals:

```text
cloud SaaS
teacher dashboard
mobile app
automatic email/submission
shell command automation
OpenClaw integration
merged upstream codebase
```

### Build order

```text
1. StudyOps Core DB + API
2. Web Shell onboarding
3. DeepTutor document/quiz loop
4. Weak topic + task planning loop
5. Hermes daily coach
6. Hermes weekly review
7. Approval execution
8. Hardening/demo polish
```

### MVP success definition

StudyOps succeeds when it can demonstrate one complete evidence-backed learning loop:

```text
A student uploads course material, learns through Q&A and quiz,
StudyOps detects weak topics,
creates daily study tasks,
runs an autonomous weekly review across course/project/career tracks,
proposes a plan adjustment with evidence,
and applies it only after approval.
```
