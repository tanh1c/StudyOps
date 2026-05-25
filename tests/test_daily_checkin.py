from fastapi.testclient import TestClient

from studyops_core.main import app


def test_run_daily_checkin_creates_job(client_session):
    client = TestClient(app)
    response = client.post('/autonomy/jobs/run', json={'job_type': 'daily_checkin', 'reason': 'manual_run'})

    assert response.status_code == 200
    data = response.json()
    assert data['job_type'] == 'daily_checkin'
    assert data['status'] == 'succeeded'
