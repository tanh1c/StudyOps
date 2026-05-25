from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from studyops_core.deps import get_session
from studyops_core.models import StudyTask, Track
from studyops_core.schemas import StudyTaskCreate
from studyops_core.services.events import record_event

router = APIRouter()


@router.post('/tasks')
def create_task(payload: StudyTaskCreate, session: Session = Depends(get_session)):
    if session.get(Track, payload.track_id) is None:
        raise HTTPException(status_code=404, detail='Track not found')
    task = StudyTask(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    task_data = task.model_dump()
    record_event(session, event_type='study_task.created', actor=task.created_by, payload={'track_id': task.track_id, 'task_id': task.id})
    return task_data


@router.get('/tracks/{track_id}/tasks')
def list_track_tasks(track_id: int, session: Session = Depends(get_session)):
    return session.exec(select(StudyTask).where(StudyTask.track_id == track_id)).all()


@router.post('/tasks/{task_id}/complete')
def complete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(StudyTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    task.status = 'done'
    session.add(task)
    session.commit()
    session.refresh(task)
    task_data = task.model_dump()
    record_event(session, event_type='study_task.completed', actor='user', payload={'track_id': task.track_id, 'task_id': task.id})
    return task_data


@router.post('/tasks/{task_id}/skip')
def skip_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(StudyTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    task.status = 'skipped'
    session.add(task)
    session.commit()
    session.refresh(task)
    task_data = task.model_dump()
    record_event(session, event_type='study_task.skipped', actor='user', payload={'track_id': task.track_id, 'task_id': task.id})
    return task_data
