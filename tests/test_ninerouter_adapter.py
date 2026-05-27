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


def test_ninerouter_create_chat_completion_posts_openai_payload(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured['url'] = url
        captured['headers'] = headers
        captured['json'] = json
        captured['timeout'] = timeout
        request = httpx.Request('POST', url)
        return httpx.Response(
            200,
            request=request,
            json={
                'id': 'chatcmpl_1',
                'choices': [{'message': {'role': 'assistant', 'content': 'Xin chào'}}],
            },
        )

    monkeypatch.setattr(httpx, 'post', fake_post)

    result = NineRouterAdapter(base_url='http://localhost:20128', api_key='sk-test').create_chat_completion(
        model='openai/gpt-4o-mini',
        messages=[{'role': 'user', 'content': 'Chào'}],
        temperature=0.2,
        max_tokens=128,
    )

    assert captured == {
        'url': 'http://localhost:20128/v1/chat/completions',
        'headers': {'Authorization': 'Bearer sk-test'},
        'json': {
            'model': 'openai/gpt-4o-mini',
            'messages': [{'role': 'user', 'content': 'Chào'}],
            'temperature': 0.2,
            'max_tokens': 128,
        },
        'timeout': 5.0,
    }
    assert result['choices'][0]['message']['content'] == 'Xin chào'


def test_ninerouter_create_chat_completion_omits_optional_fields(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured['json'] = json
        request = httpx.Request('POST', url)
        return httpx.Response(200, request=request, json={'choices': []})

    monkeypatch.setattr(httpx, 'post', fake_post)

    NineRouterAdapter(base_url='http://localhost:20128', api_key=None).create_chat_completion(
        model='openai/gpt-4o-mini',
        messages=[{'role': 'user', 'content': 'Chào'}],
    )

    assert captured['json'] == {
        'model': 'openai/gpt-4o-mini',
        'messages': [{'role': 'user', 'content': 'Chào'}],
    }
