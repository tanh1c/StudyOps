from fastapi.testclient import TestClient

from studyops_core.main import app


def test_upload_and_ask_knowledge_item(client_session):
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()

    upload = client.post(f"/tracks/{track['id']}/knowledge/upload", json={'title': 'Lecture 3', 'source_type': 'pdf'})
    assert upload.status_code == 200
    knowledge = upload.json()
    assert knowledge['status'] == 'ready'

    ask = client.post(f"/knowledge/{knowledge['id']}/ask", json={'question': 'Apriori là gì?', 'language': 'vi'})
    assert ask.status_code == 200
    assert ask.json()['citations']
