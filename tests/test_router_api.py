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

    def create_chat_completion(self, *, model, messages, temperature=None, max_tokens=None):
        return {
            'id': 'chatcmpl_test',
            'model': model,
            'choices': [
                {
                    'message': {
                        'role': 'assistant',
                        'content': f"reply to {messages[-1]['content']}",
                    }
                }
            ],
            'temperature': temperature,
            'max_tokens': max_tokens,
        }


class FailingRouterAdapter:
    def list_model_groups(self):
        request = httpx.Request('GET', 'http://localhost:20128/v1/models')
        response = httpx.Response(401, request=request, json={'error': 'Unauthorized'})
        raise httpx.HTTPStatusError('Unauthorized', request=request, response=response)

    def create_chat_completion(self, *, model, messages, temperature=None, max_tokens=None):
        request = httpx.Request('POST', 'http://localhost:20128/v1/chat/completions')
        response = httpx.Response(400, request=request, json={'error': 'Invalid model format'})
        raise httpx.HTTPStatusError('Invalid model format', request=request, response=response)


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


def test_router_chat_completions_returns_upstream_response(monkeypatch):
    monkeypatch.setattr(router, 'get_router_adapter', lambda: StubRouterAdapter())
    client = TestClient(app)

    response = client.post(
        '/router/chat/completions',
        json={
            'model': 'openai/gpt-4o-mini',
            'messages': [{'role': 'user', 'content': 'Chào'}],
            'temperature': 0.2,
            'max_tokens': 128,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        'id': 'chatcmpl_test',
        'model': 'openai/gpt-4o-mini',
        'choices': [{'message': {'role': 'assistant', 'content': 'reply to Chào'}}],
        'temperature': 0.2,
        'max_tokens': 128,
    }


def test_router_chat_completions_rejects_empty_messages(monkeypatch):
    monkeypatch.setattr(router, 'get_router_adapter', lambda: StubRouterAdapter())
    client = TestClient(app)

    response = client.post(
        '/router/chat/completions',
        json={'model': 'openai/gpt-4o-mini', 'messages': []},
    )

    assert response.status_code == 422


def test_router_chat_completions_maps_router_error_to_bad_gateway(monkeypatch):
    monkeypatch.setattr(router, 'get_router_adapter', lambda: FailingRouterAdapter())
    client = TestClient(app)

    response = client.post(
        '/router/chat/completions',
        json={
            'model': 'bad-model',
            'messages': [{'role': 'user', 'content': 'Chào'}],
        },
    )

    assert response.status_code == 502
    assert response.json()['detail'] == {
        'status': 'unavailable',
        'code': 400,
        'message': 'Invalid model format',
    }
