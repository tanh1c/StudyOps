from datetime import datetime, timezone

from studyops_core.models import EventLog, Track


def test_track_has_required_fields():
    track = Track(title='Calculus', type='course')

    assert track.title == 'Calculus'
    assert track.type == 'course'


def test_event_log_has_timestamp():
    event = EventLog(event_type='track.created', actor='user', payload={'track': 'Calculus'})

    assert event.event_type == 'track.created'
    assert event.actor == 'user'
    assert event.payload == {'track': 'Calculus'}
    assert isinstance(event.created_at, datetime)
    assert event.created_at.tzinfo == timezone.utc
