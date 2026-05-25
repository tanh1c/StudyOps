from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from studyops_core.deps import get_session
from studyops_core.models import UserProfile
from studyops_core.schemas import UserProfileUpsert
from studyops_core.services.events import record_event

router = APIRouter()


@router.get('/profile')
def get_profile(session: Session = Depends(get_session)):
    return session.exec(select(UserProfile)).first()


@router.put('/profile')
def upsert_profile(payload: UserProfileUpsert, session: Session = Depends(get_session)):
    profile = session.exec(select(UserProfile)).first()
    event_type = 'profile.updated'
    if profile is None:
        profile = UserProfile(**payload.model_dump())
        event_type = 'profile.created'
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)

    session.add(profile)
    session.commit()
    session.refresh(profile)
    profile_data = profile.model_dump()
    record_event(session, event_type=event_type, actor='user', payload={'profile_id': profile.id})
    return profile_data
