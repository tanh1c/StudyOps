from datetime import datetime, timezone

from sqlmodel import Session, select

from studyops_core.adapters.hermes import HermesAdapter
from studyops_core.adapters.mock import MockHermesAdapter
from studyops_core.config import settings
from studyops_core.models import AutonomyJob, Track
from studyops_core.services import llm
from studyops_core.services.proposals import create_proposal_with_policy


def get_hermes_adapter():
    return HermesAdapter() if settings.hermes_enabled else MockHermesAdapter()


def run_daily_checkin(*, session: Session, user_id: str = 'usr_local', reason: str = 'manual_run') -> AutonomyJob:
    now = datetime.now(timezone.utc)
    job = AutonomyJob(
        user_id=user_id,
        job_type='daily_checkin',
        status='running',
        reason=reason,
        scheduled_for=now,
        started_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    tracks = session.exec(select(Track)).all()
    snapshot = {'active_tracks': [track.model_dump() for track in tracks]}
    output = get_hermes_adapter().run_daily_checkin(snapshot) if settings.hermes_enabled else run_llm_daily_checkin(snapshot)

    for proposal_data in output.get('proposals', []):
        create_proposal_with_policy(session=session, user_id=user_id, **proposal_data)

    return _complete_job(session, job, snapshot, output)


def run_llm_daily_checkin(snapshot: dict) -> dict:
    completion = llm.chat_with_model(
        messages=[
            {
                'role': 'system',
                'content': 'Bạn là StudyOps Mentor. Trả lời ngắn gọn bằng tiếng Việt, tập trung vào kế hoạch học hôm nay.',
            },
            {
                'role': 'user',
                'content': f'Tạo daily check-in dựa trên snapshot này: {snapshot}',
            },
        ],
        temperature=0.3,
        max_tokens=500,
    )
    return {'job_summary': llm.extract_assistant_text(completion), 'messages': [], 'proposals': []}



def _complete_job(session: Session, job: AutonomyJob, snapshot: dict, output: dict) -> AutonomyJob:
    job.input_snapshot = snapshot
    job.output = output
    job.output_summary = output.get('job_summary')
    job.status = 'succeeded'
    job.completed_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def run_weekly_review(*, session: Session, user_id: str = 'usr_local', reason: str = 'manual_run') -> AutonomyJob:
    now = datetime.now(timezone.utc)
    job = AutonomyJob(
        user_id=user_id,
        job_type='weekly_review',
        status='running',
        reason=reason,
        scheduled_for=now,
        started_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    tracks = session.exec(select(Track)).all()
    snapshot = {'active_tracks': [track.model_dump() for track in tracks]}
    output = get_hermes_adapter().run_weekly_review(snapshot)

    for proposal_data in output.get('proposals', []):
        create_proposal_with_policy(session=session, user_id=user_id, **proposal_data)

    return _complete_job(session, job, snapshot, output)


def run_plan_rebalance(
    *, session: Session, instruction: str, user_id: str = 'usr_local', reason: str = 'manual_run'
) -> AutonomyJob:
    now = datetime.now(timezone.utc)
    job = AutonomyJob(
        user_id=user_id,
        job_type='plan_rebalance',
        status='running',
        reason=reason,
        scheduled_for=now,
        started_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    tracks = session.exec(select(Track)).all()
    snapshot = {'active_tracks': [track.model_dump() for track in tracks], 'instruction': instruction}
    output = get_hermes_adapter().run_plan_rebalance(snapshot, instruction)

    for proposal_data in output.get('proposals', []):
        create_proposal_with_policy(session=session, user_id=user_id, **proposal_data)

    return _complete_job(session, job, snapshot, output)
