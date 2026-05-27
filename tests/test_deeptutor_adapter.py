import json
from pathlib import Path
import subprocess

import httpx
import pytest

from studyops_core.adapters.deeptutor import DeepTutorAdapter


def test_deeptutor_health_maps_ok(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured['url'] = url
        request = httpx.Request('GET', url)
        return httpx.Response(200, request=request, json={'status': 'ok'})

    monkeypatch.setattr(httpx, 'get', fake_get)

    result = DeepTutorAdapter(base_url='http://localhost:8001').health_check()

    assert result['status'] == 'ok'
    assert captured['url'] == 'http://localhost:8001/api/v1/knowledge/health'


def test_deeptutor_create_or_get_kb_returns_existing_status(monkeypatch):
    def fake_get(url, timeout):
        request = httpx.Request('GET', url)
        return httpx.Response(200, request=request, json={'status': 'ready'})

    monkeypatch.setattr(httpx, 'get', fake_get)

    result = DeepTutorAdapter(base_url='http://localhost:8001').create_or_get_kb({'id': 7, 'title': 'Data Mining'})

    assert result == {'deeptutor_kb_id': 'studyops-7-data-mining', 'status': 'ready'}


def test_deeptutor_create_or_get_kb_returns_missing_for_404(monkeypatch):
    def fake_get(url, timeout):
        request = httpx.Request('GET', url)
        return httpx.Response(404, request=request, json={'detail': 'not found'})

    monkeypatch.setattr(httpx, 'get', fake_get)

    result = DeepTutorAdapter(base_url='http://localhost:8001').create_or_get_kb({'id': 7, 'title': 'Data Mining'})

    assert result == {'deeptutor_kb_id': 'studyops-7-data-mining', 'status': 'missing'}


def test_deeptutor_upload_document_creates_missing_kb(monkeypatch, tmp_path: Path):
    file_path = tmp_path / 'lecture.md'
    file_path.write_text('hello', encoding='utf-8')
    calls = []

    def fake_get(url, timeout):
        request = httpx.Request('GET', url)
        return httpx.Response(404, request=request, json={'detail': 'not found'})

    def fake_post(url, data=None, files=None, timeout=None):
        calls.append({'url': url, 'data': data, 'filename': files[0][1][0]})
        request = httpx.Request('POST', url)
        return httpx.Response(200, request=request, json={'files': ['lecture.md'], 'task_id': 'task-1'})

    monkeypatch.setattr(httpx, 'get', fake_get)
    monkeypatch.setattr(httpx, 'post', fake_post)

    result = DeepTutorAdapter(base_url='http://localhost:8001').upload_document(
        track_id='7',
        kb_id='studyops-7-data-mining',
        file_path=str(file_path),
        title='lecture.md',
    )

    assert calls[0]['url'] == 'http://localhost:8001/api/v1/knowledge/create'
    assert calls[0]['data'] == {'name': 'studyops-7-data-mining', 'rag_provider': 'llamaindex'}
    assert result['deeptutor_document_id'] == 'lecture.md'
    assert result['status'] == 'processing'


def test_deeptutor_upload_document_posts_to_existing_kb(monkeypatch, tmp_path: Path):
    file_path = tmp_path / 'lecture.md'
    file_path.write_text('hello', encoding='utf-8')
    calls = []

    def fake_get(url, timeout):
        request = httpx.Request('GET', url)
        return httpx.Response(200, request=request, json={'status': 'ready'})

    def fake_post(url, files=None, timeout=None):
        calls.append({'url': url, 'filename': files[0][1][0]})
        request = httpx.Request('POST', url)
        return httpx.Response(200, request=request, json={'files': ['lecture.md'], 'task_id': 'task-2'})

    monkeypatch.setattr(httpx, 'get', fake_get)
    monkeypatch.setattr(httpx, 'post', fake_post)

    result = DeepTutorAdapter(base_url='http://localhost:8001').upload_document(
        track_id='7',
        kb_id='studyops-7-data-mining',
        file_path=str(file_path),
        title='lecture.md',
    )

    assert calls[0]['url'] == 'http://localhost:8001/api/v1/knowledge/studyops-7-data-mining/upload'
    assert result['task_id'] == 'task-2'


def test_deeptutor_ask_document_uses_cli_json(monkeypatch):
    captured = {}

    def fake_run(command, capture_output, text, check, timeout):
        captured['command'] = command
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps({'content': 'Apriori là thuật toán...', 'sources': [{'title': 'lecture'}]}), stderr='')

    monkeypatch.setattr(subprocess, 'run', fake_run)

    result = DeepTutorAdapter(base_url='http://localhost:8001').ask_document(
        kb_id='studyops-7-data-mining', question='Apriori là gì?', language='vi'
    )

    assert captured['command'] == [
        'deeptutor',
        'run',
        'chat',
        'Apriori là gì?',
        '--kb',
        'studyops-7-data-mining',
        '--tool',
        'rag',
        '--language',
        'vi',
        '--format',
        'json',
    ]
    assert result['answer'] == 'Apriori là thuật toán...'
    assert result['citations'] == [{'title': 'lecture'}]


def test_deeptutor_generate_quiz_uses_deep_question_cli(monkeypatch):
    captured = {}

    def fake_run(command, capture_output, text, check, timeout):
        captured['command'] = command
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps({'session_id': 'quiz-session', 'questions': [{'id': 'q1'}]}), stderr='')

    monkeypatch.setattr(subprocess, 'run', fake_run)

    result = DeepTutorAdapter(base_url='http://localhost:8001').generate_quiz(
        {'topic_tags': ['association-rules'], 'question_count': 3}
    )

    assert captured['command'] == [
        'deeptutor',
        'run',
        'deep_question',
        'association-rules',
        '--config',
        'num_questions=3',
        '--format',
        'json',
    ]
    assert result['deeptutor_quiz_id'] == 'quiz-session'
    assert result['questions'] == [{'id': 'q1'}]


def test_deeptutor_cli_can_be_disabled():
    with pytest.raises(RuntimeError, match='disabled'):
        DeepTutorAdapter(cli_enabled=False).ask_document(kb_id='kb', question='q', language='vi')
