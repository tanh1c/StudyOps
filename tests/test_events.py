from sqlmodel import select

from studyops_core.models import EventLog
from studyops_core.services.events import record_event


def test_record_event_persists_event_log(session):
    event = record_event(
        session,
        event_type='track.created',
        actor='user',
        payload={'track_id': 1},
    )

    saved_event = session.exec(select(EventLog)).one()

    assert saved_event.id == event.id
    assert saved_event.event_type == 'track.created'
    assert saved_event.actor == 'user'
    assert saved_event.payload == {'track_id': 1}
