from fastapi.testclient import TestClient

from studyops_core.main import app


def test_weekly_review_creates_pending_proposal(client_session):
    client = TestClient(app)
    response = client.post('/autonomy/jobs/run', json={'job_type': 'weekly_review', 'reason': 'manual_run'})

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'succeeded'

    proposals = client.get('/proposals').json()
    assert proposals
    assert proposals[0]['status'] == 'pending'
