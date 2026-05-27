from fastapi.testclient import TestClient

from studyops_core.config import settings
from studyops_core.main import app
from studyops_core.routers import health


class StubRouterAdapter:
    def health_check(self):
        return {'status': 'ok', 'raw': {'ok': True}}


class StubDeepTutorAdapter:
    def health_check(self):
        return {'status': 'ok', 'raw': {'status': 'ok'}}


class StubHermesAdapter:
    def health_check(self):
        return {'status': 'ok', 'raw': {'gateway': 'ready'}}


def test_services_health_returns_service_statuses(monkeypatch):
    monkeypatch.setattr(health, 'get_router_adapter', lambda: StubRouterAdapter())
    monkeypatch.setattr(health, 'get_deeptutor_adapter', lambda: StubDeepTutorAdapter())
    client = TestClient(app)
    response = client.get('/health/services')

    assert response.status_code == 200
    data = response.json()
    assert data['studyops_core'] == 'ok'
    assert data['deeptutor'] == 'ok'
    assert data['deeptutor_detail'] == {'status': 'ok', 'raw': {'status': 'ok'}}
    assert data['hermes'] == 'mock'
    assert data['hermes_detail'] == {'status': 'mock', 'enabled': False}
    assert data['router'] == 'ok'
    assert data['router_detail'] == {'status': 'ok', 'raw': {'ok': True}}


def test_services_health_checks_real_hermes_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, 'hermes_enabled', True)
    monkeypatch.setattr(health, 'get_router_adapter', lambda: StubRouterAdapter())
    monkeypatch.setattr(health, 'get_deeptutor_adapter', lambda: StubDeepTutorAdapter())
    monkeypatch.setattr(health, 'get_hermes_adapter', lambda: StubHermesAdapter())
    client = TestClient(app)
    response = client.get('/health/services')

    assert response.status_code == 200
    data = response.json()
    assert data['hermes'] == 'ok'
    assert data['hermes_detail'] == {'status': 'ok', 'raw': {'gateway': 'ready'}}
