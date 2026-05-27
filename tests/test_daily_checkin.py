from fastapi.testclient import TestClient

from studyops_core.config import settings
from studyops_core.main import app
from studyops_core.services import autonomy


def test_run_daily_checkin_creates_job(client_session, monkeypatch):
    monkeypatch.setattr(
        autonomy,
        'run_llm_daily_checkin',
        lambda snapshot: {'job_summary': 'Hôm nay hãy ôn Data Mining.', 'messages': [], 'proposals': []},
    )
    client = TestClient(app)
    response = client.post('/autonomy/jobs/run', json={'job_type': 'daily_checkin', 'reason': 'manual_run'})

    assert response.status_code == 200
    data = response.json()
    assert data['job_type'] == 'daily_checkin'
    assert data['status'] == 'succeeded'
    assert data['output_summary'] == 'Hôm nay hãy ôn Data Mining.'


def test_daily_checkin_uses_hermes_when_enabled(client_session, monkeypatch):
    class StubHermesAdapter:
        def run_daily_checkin(self, snapshot):
            return {'job_summary': 'Hermes daily', 'messages': [], 'proposals': []}

    monkeypatch.setattr(settings, 'hermes_enabled', True)
    monkeypatch.setattr(autonomy, 'get_hermes_adapter', lambda: StubHermesAdapter())
    client = TestClient(app)
    response = client.post('/autonomy/jobs/run', json={'job_type': 'daily_checkin', 'reason': 'manual_run'})

    assert response.status_code == 200
    assert response.json()['output_summary'] == 'Hermes daily'


def test_run_llm_daily_checkin_uses_llm_service(monkeypatch):
    captured = {}

    def fake_chat_with_model(*, messages, temperature=None, max_tokens=None, **kwargs):
        captured['messages'] = messages
        captured['temperature'] = temperature
        captured['max_tokens'] = max_tokens
        return {'choices': [{'message': {'content': 'Daily mentor summary'}}]}

    monkeypatch.setattr(autonomy.llm, 'chat_with_model', fake_chat_with_model)

    result = autonomy.run_llm_daily_checkin({'active_tracks': [{'title': 'Data Mining'}]})

    assert result == {'job_summary': 'Daily mentor summary', 'messages': [], 'proposals': []}
    assert captured['messages'][0]['role'] == 'system'
    assert 'Data Mining' in captured['messages'][1]['content']
    assert captured['temperature'] == 0.3
    assert captured['max_tokens'] == 500
