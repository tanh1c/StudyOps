from fastapi.testclient import TestClient

from studyops_core.main import app


def test_create_complete_and_skip_task(client_session):
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()
    task_response = client.post('/tasks', json={
        'track_id': track['id'],
        'title': 'Review Apriori',
        'task_type': 'review',
        'estimated_minutes': 25,
    })
    assert task_response.status_code == 200
    task = task_response.json()

    complete = client.post(f"/tasks/{task['id']}/complete")
    assert complete.status_code == 200
    assert complete.json()['status'] == 'done'
