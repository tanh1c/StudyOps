from datetime import datetime, timezone

from sqlmodel import Session, select

from studyops_core.adapters.mock import MockHermesAdapter
from studyops_core.models import AutonomyJob, Track
from studyops_core.services.events import record_event


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
    output = MockHermesAdapter().run_daily_checkin(snapshot)

    job.input_snapshot = snapshot
    job.output = output
    job.output_summary = output.get('job_summary')
    job.status = 'succeeded'
    job.completed_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
