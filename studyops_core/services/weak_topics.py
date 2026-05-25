from sqlmodel import Session, select

from studyops_core.models import WeakTopic


def severity_from_score(score: float) -> str:
    if score < 50:
        return 'high'
    if score < 70:
        return 'medium'
    return 'low'


def update_weak_topics_from_quiz(
    *,
    session: Session,
    track_id: int,
    topics: list[str],
    score: float,
    evidence_event_id: int,
) -> list[WeakTopic]:
    updated = []
    severity = severity_from_score(score)
    for topic in topics:
        weak_topic = session.exec(
            select(WeakTopic).where(WeakTopic.track_id == track_id, WeakTopic.topic == topic)
        ).first()
        if weak_topic is None:
            weak_topic = WeakTopic(
                track_id=track_id,
                topic=topic,
                severity=severity,
                evidence_event_ids=[evidence_event_id],
            )
        else:
            weak_topic.severity = severity
            weak_topic.evidence_event_ids = sorted(set(weak_topic.evidence_event_ids + [evidence_event_id]))
        session.add(weak_topic)
        updated.append(weak_topic)

    session.commit()
    for item in updated:
        session.refresh(item)
    return updated
