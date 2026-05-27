from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from studyops_core.adapters.deeptutor import DeepTutorAdapter
from studyops_core.deps import get_session
from studyops_core.models import KnowledgeItem, Track
from studyops_core.schemas import KnowledgeAsk, KnowledgeUpload
from studyops_core.services.events import record_event

router = APIRouter()


def get_deeptutor_adapter():
    return DeepTutorAdapter()


@router.post('/tracks/{track_id}/knowledge/upload')
def upload_knowledge(track_id: int, payload: KnowledgeUpload, session: Session = Depends(get_session)):
    track = session.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail='Track not found')

    adapter = get_deeptutor_adapter()
    kb = adapter.create_or_get_kb(track.model_dump())
    doc = adapter.upload_document(
        track_id=str(track_id),
        kb_id=kb['deeptutor_kb_id'],
        file_path=payload.source_uri or '',
        title=payload.title,
    )
    item = KnowledgeItem(
        track_id=track_id,
        title=payload.title,
        source_type=payload.source_type,
        source_uri=payload.source_uri,
        deeptutor_kb_id=kb['deeptutor_kb_id'],
        deeptutor_document_id=doc['deeptutor_document_id'],
        deeptutor_task_id=doc.get('task_id'),
        status=doc['status'],
        progress={'upload': doc.get('raw') or {}, 'task_id': doc.get('task_id')},
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    item_data = item.model_dump()
    record_event(session, event_type='knowledge.uploaded', actor='user', payload={'track_id': track_id, 'knowledge_item_id': item.id})
    return item_data


@router.get('/knowledge/{knowledge_item_id}/status')
def refresh_knowledge_status(knowledge_item_id: int, session: Session = Depends(get_session)):
    item = session.get(KnowledgeItem, knowledge_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Knowledge item not found')
    if item.deeptutor_kb_id:
        result = get_deeptutor_adapter().get_document_progress(
            kb_id=item.deeptutor_kb_id,
            has_task=bool(item.deeptutor_task_id),
        )
        item.status = result['status']
        item.progress = result['progress']
        session.add(item)
        session.commit()
        session.refresh(item)
    return item.model_dump()


@router.post('/knowledge/{knowledge_item_id}/ask')
def ask_knowledge(knowledge_item_id: int, payload: KnowledgeAsk, session: Session = Depends(get_session)):
    item = session.get(KnowledgeItem, knowledge_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Knowledge item not found')
    if item.status != 'ready':
        raise HTTPException(status_code=409, detail='Knowledge item is not ready')

    result = get_deeptutor_adapter().ask_document(
        kb_id=item.deeptutor_kb_id or '',
        question=payload.question,
        language=payload.language,
    )
    record_event(
        session,
        event_type='knowledge.asked',
        actor='user',
        payload={'track_id': item.track_id, 'knowledge_item_id': item.id, 'question': payload.question},
    )
    return {**result, 'mentor_guidance': None, 'knowledge_query_id': None}
