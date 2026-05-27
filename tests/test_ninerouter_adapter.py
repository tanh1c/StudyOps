import httpx

from studyops_core.adapters.ninerouter import NineRouterAdapter


def test_ninerouter_health_maps_ok_response(monkeypatch):
    captured = {}

    def fake_get(url, headers, timeout):
        captured['url'] = url
        captured['headers'] = headers
        captured['timeout'] = timeout
        request = httpx.Request('GET', url)
        return httpx.Response(200, request=request, json={'ok': True})

    monkeypatch.setattr(httpx, 'get', fake_get)

    result = NineRouterAdapter(base_url='http://localhost:20128', api_key='sk-test').health_check()

    assert result['status'] == 'ok'
    assert captured['url'] == 'http://localhost:20128/api/health'
    assert captured['headers'] == {'Authorization': 'Bearer sk-test'}
    assert captured['timeout'] == 5.0


def test_ninerouter_omits_auth_when_key_missing(monkeypatch):
    captured = {}

    def fake_get(url, headers, timeout):
        captured['headers'] = headers
        request = httpx.Request('GET', url)
        return httpx.Response(200, request=request, json={'ok': True})

    monkeypatch.setattr(httpx, 'get', fake_get)

    NineRouterAdapter(base_url='http://localhost:20128', api_key='').health_check()

    assert captured['headers'] == {}


def test_ninerouter_health_maps_http_error(monkeypatch):
    def fake_get(url, headers, timeout):
        request = httpx.Request('GET', url)
        return httpx.Response(401, request=request, json={'error': 'Unauthorized'})

    monkeypatch.setattr(httpx, 'get', fake_get)

    result = NineRouterAdapter(base_url='http://localhost:20128', api_key='bad-key').health_check()

    assert result == {'status': 'unavailable', 'code': 401, 'detail': 'Unauthorized'}


def test_ninerouter_list_models_uses_v1_models(monkeypatch):
    def fake_get(url, headers, timeout):
        assert url == 'http://localhost:20128/v1/models'
        request = httpx.Request('GET', url)
        return httpx.Response(200, request=request, json={'data': [{'id': 'openai/gpt-4o-mini'}]})

    monkeypatch.setattr(httpx, 'get', fake_get)

    result = NineRouterAdapter(base_url='http://localhost:20128', api_key=None).list_models()

    assert result['models'] == [{'id': 'openai/gpt-4o-mini'}]


def test_ninerouter_list_model_groups_calls_all_model_endpoints(monkeypatch):
    captured_urls = []

    def fake_get(url, headers, timeout):
        captured_urls.append(url)
        request = httpx.Request('GET', url)
        model_id = url.rsplit('/', 1)[-1]
        if url.endswith('/v1/models'):
            model_id = 'chat'
        return httpx.Response(200, request=request, json={'data': [{'id': f'{model_id}-model'}]})

    monkeypatch.setattr(httpx, 'get', fake_get)

    result = NineRouterAdapter(base_url='http://localhost:20128', api_key=None).list_model_groups()

    assert captured_urls == [
        'http://localhost:20128/v1/models',
        'http://localhost:20128/v1/models/image',
        'http://localhost:20128/v1/models/tts',
        'http://localhost:20128/v1/models/embedding',
        'http://localhost:20128/v1/models/web',
        'http://localhost:20128/v1/models/stt',
        'http://localhost:20128/v1/models/image-to-text',
    ]
    assert result == {
        'chat': [{'id': 'chat-model'}],
        'image': [{'id': 'image-model'}],
        'tts': [{'id': 'tts-model'}],
        'embedding': [{'id': 'embedding-model'}],
        'web': [{'id': 'web-model'}],
        'stt': [{'id': 'stt-model'}],
        'image_to_text': [{'id': 'image-to-text-model'}],
    }
