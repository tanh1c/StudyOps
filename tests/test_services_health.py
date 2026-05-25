from fastapi.testclient import TestClient

from studyops_core.main import app


def test_services_health_returns_service_statuses():
    client = TestClient(app)
    response = client.get('/health/services')

    assert response.status_code == 200
    data = response.json()
    assert data['studyops_core'] == 'ok'
    assert data['router'] == 'ok'
