from fastapi.testclient import TestClient

from studyops_core.main import app


def test_create_track_goal_and_deadline(client_session):
    client = TestClient(app)
    track_response = client.post('/tracks', json={
        'user_id': 'usr_local',
        'type': 'course',
        'title': 'Data Mining',
        'priority': 'high',
    })
    assert track_response.status_code == 200
    track = track_response.json()

    goal_response = client.post(f"/tracks/{track['id']}/goals", json={
        'title': 'Score 8/10 on midterm',
        'success_criteria': '>=80% quiz score before exam',
    })
    assert goal_response.status_code == 200

    deadline_response = client.post(f"/tracks/{track['id']}/deadlines", json={
        'title': 'Data Mining Midterm',
        'due_at': '2026-06-15T08:00:00+07:00',
        'type': 'exam',
        'importance': 'critical',
    })
    assert deadline_response.status_code == 200
