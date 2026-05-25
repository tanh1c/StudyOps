from studyops_core.adapters.mock import MockDeepTutorAdapter, MockHermesAdapter, MockRouterAdapter


def test_mock_deeptutor_ask_returns_citations():
    adapter = MockDeepTutorAdapter()
    result = adapter.ask_document(kb_id='kb_1', question='Apriori là gì?', language='vi')
    assert result['answer']
    assert result['citations']


def test_mock_hermes_weekly_review_returns_proposals():
    adapter = MockHermesAdapter()
    result = adapter.run_weekly_review({'active_tracks': []})
    assert 'proposals' in result


def test_mock_router_health_is_ok():
    adapter = MockRouterAdapter()
    assert adapter.health_check()['status'] == 'ok'
