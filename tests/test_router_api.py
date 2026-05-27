import httpx
from fastapi.testclient import TestClient

from studyops_core.main import app
from studyops_core.routers import router


class StubRouterAdapter:
    def list_model_groups(self):
        return {
            'chat': [{'id': 'chat-model'}],
            'image': [],
            'tts': [],
            'embedding': [],
            'web': [],
            'stt': [],
            'image_to_text': [],
        }


class FailingRouterAdapter:
    def list_model_groups(self):
        request = httpx.Request('GET', 'http://localhost:20128/v1/models')
        response = httpx.Response(401, request=request, json={'error': 'Unauthorized'})
        raise httpx.HTTPStatusError('Unauthorized', request=request, response=response)


def test_router_models_returns_grouped_models(monkeypatch):
    monkeypatch.setattr(router, 'get_router_adapter', lambda: StubRouterAdapter())
    client = TestClient(app)

    response = client.get('/router/models')

    assert response.status_code == 200
    assert response.json() == {
        'models': {
            'chat': [{'id': 'chat-model'}],
            'image': [],
            'tts': [],
            'embedding': [],
            'web': [],
            'stt': [],
            'image_to_text': [],
        }
    }


def test_router_models_maps_router_error_to_bad_gateway(monkeypatch):
    monkeypatch.setattr(router, 'get_router_adapter', lambda: FailingRouterAdapter())
    client = TestClient(app)

    response = client.get('/router/models')

    assert response.status_code == 502
    assert response.json()['detail'] == {
        'status': 'unavailable',
        'code': 401,
        'message': 'Unauthorized',
    }
