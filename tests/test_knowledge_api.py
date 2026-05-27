from fastapi.testclient import TestClient

from studyops_core.main import app
from studyops_core.routers import knowledge


class StubDeepTutorAdapter:
    def __init__(self, *, upload_status='ready', progress_status='ready'):
        self.upload_status = upload_status
        self.progress_status = progress_status

    def create_or_get_kb(self, track):
        return {'deeptutor_kb_id': f"dt_kb_{track['id']}"}

    def upload_document(self, *, track_id, kb_id, file_path, title):
        task_id = 'task-1' if self.upload_status == 'processing' else None
        return {
            'deeptutor_document_id': 'dt_doc_mock',
            'status': self.upload_status,
            'task_id': task_id,
            'raw': {'task_id': task_id},
        }

    def get_document_progress(self, *, kb_id, has_task=True):
        return {
            'status': self.progress_status,
            'progress': {'stage': 'completed' if self.progress_status == 'ready' else 'processing_documents'},
        }

    def ask_document(self, *, kb_id, question, language):
        return {
            'answer': f'Answer for {question}',
            'citations': [{'title': 'Lecture'}],
            'session_id': 'session-1',
        }


def test_upload_and_ask_knowledge_item(client_session, monkeypatch):
    monkeypatch.setattr(knowledge, 'get_deeptutor_adapter', lambda: StubDeepTutorAdapter())
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()

    upload = client.post(f"/tracks/{track['id']}/knowledge/upload", json={'title': 'Lecture 3', 'source_type': 'pdf'})
    assert upload.status_code == 200
    knowledge_item = upload.json()
    assert knowledge_item['status'] == 'ready'

    ask = client.post(f"/knowledge/{knowledge_item['id']}/ask", json={'question': 'Apriori là gì?', 'language': 'vi'})
    assert ask.status_code == 200
    assert ask.json()['citations']


def test_upload_persists_deeptutor_task_progress(client_session, monkeypatch):
    monkeypatch.setattr(knowledge, 'get_deeptutor_adapter', lambda: StubDeepTutorAdapter(upload_status='processing'))
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()

    upload = client.post(f"/tracks/{track['id']}/knowledge/upload", json={'title': 'Lecture 3', 'source_type': 'pdf'})

    assert upload.status_code == 200
    knowledge_item = upload.json()
    assert knowledge_item['status'] == 'processing'
    assert knowledge_item['deeptutor_task_id'] == 'task-1'
    assert knowledge_item['progress']['task_id'] == 'task-1'


def test_refresh_knowledge_status_transitions_to_ready(client_session, monkeypatch):
    monkeypatch.setattr(knowledge, 'get_deeptutor_adapter', lambda: StubDeepTutorAdapter(upload_status='processing'))
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()
    knowledge_item = client.post(
        f"/tracks/{track['id']}/knowledge/upload",
        json={'title': 'Lecture 3', 'source_type': 'pdf'},
    ).json()

    status = client.get(f"/knowledge/{knowledge_item['id']}/status")

    assert status.status_code == 200
    assert status.json()['status'] == 'ready'
    assert status.json()['progress']['stage'] == 'completed'


def test_ask_waits_until_knowledge_status_is_ready(client_session, monkeypatch):
    monkeypatch.setattr(knowledge, 'get_deeptutor_adapter', lambda: StubDeepTutorAdapter(upload_status='processing'))
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()
    knowledge_item = client.post(
        f"/tracks/{track['id']}/knowledge/upload",
        json={'title': 'Lecture 3', 'source_type': 'pdf'},
    ).json()

    blocked = client.post(f"/knowledge/{knowledge_item['id']}/ask", json={'question': 'Apriori là gì?', 'language': 'vi'})
    refreshed = client.get(f"/knowledge/{knowledge_item['id']}/status")
    ask = client.post(f"/knowledge/{knowledge_item['id']}/ask", json={'question': 'Apriori là gì?', 'language': 'vi'})

    assert blocked.status_code == 409
    assert refreshed.json()['status'] == 'ready'
    assert ask.status_code == 200
    assert ask.json()['citations']
