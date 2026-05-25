from fastapi.testclient import TestClient

from studyops_core.main import app


def test_approve_proposal_marks_it_approved(client_session):
    client = TestClient(app)
    client.post('/autonomy/jobs/run', json={'job_type': 'weekly_review', 'reason': 'manual_run'})
    proposal = client.get('/proposals').json()[0]

    response = client.post(f"/proposals/{proposal['id']}/approve")
    assert response.status_code == 200
    assert response.json()['status'] == 'approved'
