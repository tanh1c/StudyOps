from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from studyops_core.deps import get_session
from studyops_core.schemas import AutonomyRunRequest
from studyops_core.services.autonomy import run_daily_checkin
from studyops_core.services.events import record_event

router = APIRouter()


@router.post('/autonomy/jobs/run')
def run_autonomy_job(payload: AutonomyRunRequest, session: Session = Depends(get_session)):
    if payload.job_type == 'daily_checkin':
        job = run_daily_checkin(session=session, reason=payload.reason)
        job_data = job.model_dump()
        record_event(session, event_type='daily_checkin.completed', actor='hermes', payload={'user_id': job.user_id, 'job_id': job.id})
        return job_data
    raise HTTPException(status_code=400, detail='Unsupported job type')
