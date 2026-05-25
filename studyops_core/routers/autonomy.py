from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from studyops_core.deps import get_session
from studyops_core.models import AgentProposal
from studyops_core.schemas import AutonomyRunRequest
from studyops_core.services.autonomy import run_daily_checkin, run_weekly_review
from studyops_core.services.events import record_event

router = APIRouter()


@router.post('/autonomy/jobs/run')
def run_autonomy_job(payload: AutonomyRunRequest, session: Session = Depends(get_session)):
    if payload.job_type == 'daily_checkin':
        job = run_daily_checkin(session=session, reason=payload.reason)
        job_data = job.model_dump()
        record_event(session, event_type='daily_checkin.completed', actor='hermes', payload={'user_id': job.user_id, 'job_id': job.id})
        return job_data
    if payload.job_type == 'weekly_review':
        job = run_weekly_review(session=session, reason=payload.reason)
        job_data = job.model_dump()
        record_event(session, event_type='weekly_review.completed', actor='hermes', payload={'user_id': job.user_id, 'job_id': job.id})
        return job_data
    raise HTTPException(status_code=400, detail='Unsupported job type')


@router.get('/proposals')
def list_proposals(session: Session = Depends(get_session)):
    return session.exec(select(AgentProposal)).all()


@router.post('/proposals/{proposal_id}/approve')
def approve_proposal(proposal_id: int, session: Session = Depends(get_session)):
    proposal = session.get(AgentProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail='Proposal not found')
    proposal.status = 'approved'
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    proposal_data = proposal.model_dump()
    record_event(session, event_type='approval.accepted', actor='user', payload={'user_id': proposal.user_id, 'proposal_id': proposal.id})
    return proposal_data


@router.post('/proposals/{proposal_id}/reject')
def reject_proposal(proposal_id: int, session: Session = Depends(get_session)):
    proposal = session.get(AgentProposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail='Proposal not found')
    proposal.status = 'rejected'
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    proposal_data = proposal.model_dump()
    record_event(session, event_type='approval.rejected', actor='user', payload={'user_id': proposal.user_id, 'proposal_id': proposal.id})
    return proposal_data
