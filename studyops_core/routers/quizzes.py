from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from studyops_core.adapters.mock import MockDeepTutorAdapter
from studyops_core.deps import get_session
from studyops_core.models import Quiz, QuizAttempt, Track
from studyops_core.schemas import QuizAttemptCreate, QuizGenerate
from studyops_core.services.events import record_event
from studyops_core.services.weak_topics import update_weak_topics_from_quiz

router = APIRouter()


@router.post('/tracks/{track_id}/quizzes/generate')
def generate_quiz(track_id: int, payload: QuizGenerate, session: Session = Depends(get_session)):
    if session.get(Track, track_id) is None:
        raise HTTPException(status_code=404, detail='Track not found')

    result = MockDeepTutorAdapter().generate_quiz(payload.model_dump())
    quiz = Quiz(
        track_id=track_id,
        title='Generated quiz',
        source_knowledge_item_ids=payload.knowledge_item_ids,
        topic_tags=payload.topic_tags,
        difficulty=payload.difficulty,
        question_count=payload.question_count,
        deeptutor_quiz_id=result['deeptutor_quiz_id'],
    )
    session.add(quiz)
    session.commit()
    session.refresh(quiz)
    quiz_data = quiz.model_dump()
    record_event(session, event_type='quiz.generated', actor='user', payload={'track_id': track_id, 'quiz_id': quiz.id})
    return quiz_data


@router.post('/quizzes/{quiz_id}/attempts')
def attempt_quiz(quiz_id: int, payload: QuizAttemptCreate, session: Session = Depends(get_session)):
    quiz = session.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail='Quiz not found')

    result = MockDeepTutorAdapter().grade_quiz({'deeptutor_quiz_id': quiz.deeptutor_quiz_id, 'answers': payload.answers})
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        track_id=quiz.track_id,
        user_id='usr_local',
        score=result['score'],
        correct_count=result['correct_count'],
        total_count=result['total_count'],
        mistake_topic_tags=result['mistake_topic_tags'],
        deeptutor_attempt_id=result['deeptutor_attempt_id'],
        feedback_summary=result['feedback_summary'],
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    attempt_data = attempt.model_dump()
    event = record_event(
        session,
        event_type='quiz.attempt.completed',
        actor='user',
        payload={'track_id': quiz.track_id, 'quiz_attempt_id': attempt.id, 'score': attempt.score},
    )
    weak_topics = update_weak_topics_from_quiz(
        session=session,
        track_id=quiz.track_id,
        topics=attempt.mistake_topic_tags,
        score=attempt.score or 0,
        evidence_event_id=event.id or 0,
    )
    return {**attempt_data, 'weak_topics_updated': [topic.id for topic in weak_topics]}
