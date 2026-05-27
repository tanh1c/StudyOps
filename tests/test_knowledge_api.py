from fastapi.testclient import TestClient

from studyops_core.main import app
from studyops_core.routers import knowledge


class StubDeepTutorAdapter:
    def create_or_get_kb(self, track):
        return {'deeptutor_kb_id': f"dt_kb_{track['id']}"}

    def upload_document(self, *, track_id, kb_id, file_path, title):
        return {'deeptutor_document_id': 'dt_doc_mock', 'status': 'ready'}

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
