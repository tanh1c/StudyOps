from typing import Any

from sqlmodel import Session

from studyops_core.models import EventLog


def record_event(
    session: Session,
    *,
    event_type: str,
    actor: str,
    payload: dict[str, Any] | None = None,
) -> EventLog:
    event = EventLog(event_type=event_type, actor=actor, payload=payload or {})
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
