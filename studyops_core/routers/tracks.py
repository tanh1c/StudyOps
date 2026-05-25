from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from studyops_core.deps import get_session
from studyops_core.models import Deadline, Goal, Track
from studyops_core.schemas import DeadlineCreate, GoalCreate, TrackCreate
from studyops_core.services.events import record_event

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
    track_data = track.model_dump()
    record_event(session, event_type='track.created', actor='user', payload={'track_id': track.id})
    return track_data


@router.get('/tracks/{track_id}')
def get_track(track_id: int, session: Session = Depends(get_session)):
    track = session.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail='Track not found')
    return track


@router.post('/tracks/{track_id}/goals')
def create_goal(track_id: int, payload: GoalCreate, session: Session = Depends(get_session)):
    if session.get(Track, track_id) is None:
        raise HTTPException(status_code=404, detail='Track not found')
    goal = Goal(track_id=track_id, **payload.model_dump())
    session.add(goal)
    session.commit()
    session.refresh(goal)
    goal_data = goal.model_dump()
    record_event(session, event_type='goal.created', actor='user', payload={'track_id': track_id, 'goal_id': goal.id})
    return goal_data


@router.post('/tracks/{track_id}/deadlines')
def create_deadline(track_id: int, payload: DeadlineCreate, session: Session = Depends(get_session)):
    if session.get(Track, track_id) is None:
        raise HTTPException(status_code=404, detail='Track not found')
    deadline = Deadline(track_id=track_id, **payload.model_dump())
    session.add(deadline)
    session.commit()
    session.refresh(deadline)
    deadline_data = deadline.model_dump()
    record_event(session, event_type='deadline.created', actor='user', payload={'track_id': track_id, 'deadline_id': deadline.id})
    return deadline_data
