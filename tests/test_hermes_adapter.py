import json

import pytest

from studyops_core.adapters.hermes import HermesAdapter


class FakeWebSocket:
    def __init__(self, events):
        self.events = iter(events)
        self.sent_messages = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def send(self, message):
        self.sent_messages.append(json.loads(message))

    async def recv(self):
        return json.dumps(next(self.events))


class FakeConnect:
    def __init__(self, events):
        self.websocket = FakeWebSocket(events)
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        return self.websocket


def gateway_ready():
    return {'jsonrpc': '2.0', 'method': 'event', 'params': {'type': 'gateway.ready', 'payload': {'skin': 'default'}}}


def rpc_response(request_id, result):
    return {'jsonrpc': '2.0', 'id': request_id, 'result': result}


def hermes_event(event_type, payload):
    return {'jsonrpc': '2.0', 'method': 'event', 'params': {'type': event_type, 'payload': payload}}


def test_hermes_health_check_maps_gateway_ready_to_ok(monkeypatch):
    fake_connect = FakeConnect([gateway_ready()])
    monkeypatch.setattr('studyops_core.adapters.hermes.websockets.connect', fake_connect)

    result = HermesAdapter(base_url='http://localhost:9000').health_check()

    assert fake_connect.urls == ['ws://localhost:9000/api/ws']
    assert result['status'] == 'ok'


def test_hermes_weekly_review_uses_json_rpc_and_parses_proposals(monkeypatch):
    fake_connect = FakeConnect(
        [
            gateway_ready(),
            rpc_response(1, {'session_id': 'session-1'}),
            rpc_response(2, {'status': 'streaming'}),
            hermes_event(
                'message.complete',
                {
                    'content': json.dumps(
                        {
                            'job_summary': 'Review tuần',
                            'observations': ['Cần ôn Data Mining'],
                            'track_assessments': [],
                            'proposals': [
                                {
                                    'type': 'modify_plan',
                                    'title': 'Ôn Apriori',
                                    'summary': 'Thêm buổi ôn Apriori',
                                    'reason': 'Quiz yếu topic apriori',
                                    'changes': {'actions': [{'type': 'modify_active_plan'}]},
                                }
                            ],
                        }
                    )
                },
            ),
            rpc_response(3, {'status': 'closed'}),
        ]
    )
    monkeypatch.setattr('studyops_core.adapters.hermes.websockets.connect', fake_connect)

    result = HermesAdapter(base_url='http://localhost:9000').run_weekly_review({'active_tracks': [{'title': 'Data Mining'}]})

    assert [message['method'] for message in fake_connect.websocket.sent_messages] == [
        'session.create',
        'prompt.submit',
        'session.close',
    ]
    prompt = fake_connect.websocket.sent_messages[1]['params']['prompt']
    assert 'weekly review' in prompt
    assert 'Data Mining' in prompt
    assert result['job_summary'] == 'Review tuần'
    assert result['observations'] == ['Cần ôn Data Mining']
    assert result['proposals'][0] == {
        'proposal_type': 'modify_plan',
        'title': 'Ôn Apriori',
        'summary': 'Thêm buổi ôn Apriori',
        'rationale': 'Quiz yếu topic apriori',
        'evidence_event_ids': [],
        'proposed_changes': {'actions': [{'type': 'modify_active_plan'}]},
    }


def test_hermes_prose_fallback_returns_summary_with_empty_proposals(monkeypatch):
    fake_connect = FakeConnect(
        [
            gateway_ready(),
            rpc_response(1, {'session_id': 'session-1'}),
            rpc_response(2, {'status': 'streaming'}),
            hermes_event('message.complete', {'content': 'Hôm nay chỉ cần ôn nhẹ.'}),
            rpc_response(3, {'status': 'closed'}),
        ]
    )
    monkeypatch.setattr('studyops_core.adapters.hermes.websockets.connect', fake_connect)

    result = HermesAdapter(base_url='http://localhost:9000').run_daily_checkin({'active_tracks': []})

    assert result['job_summary'] == 'Hôm nay chỉ cần ôn nhẹ.'
    assert result['proposals'] == []


def test_hermes_json_rpc_error_raises(monkeypatch):
    fake_connect = FakeConnect(
        [
            gateway_ready(),
            {'jsonrpc': '2.0', 'id': 1, 'error': {'message': 'session failed'}},
        ]
    )
    monkeypatch.setattr('studyops_core.adapters.hermes.websockets.connect', fake_connect)

    with pytest.raises(RuntimeError, match='session failed'):
        HermesAdapter(base_url='http://localhost:9000').run_daily_checkin({'active_tracks': []})
