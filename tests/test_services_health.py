from fastapi.testclient import TestClient

from studyops_core.main import app
from studyops_core.routers import health


class StubRouterAdapter:
    def health_check(self):
        return {'status': 'ok', 'raw': {'ok': True}}


def test_services_health_returns_service_statuses(monkeypatch):
    monkeypatch.setattr(health, 'get_router_adapter', lambda: StubRouterAdapter())
    client = TestClient(app)
    response = client.get('/health/services')

    assert response.status_code == 200
    data = response.json()
    assert data['studyops_core'] == 'ok'
    assert data['router'] == 'ok'
    assert data['router_detail'] == {'status': 'ok', 'raw': {'ok': True}}
