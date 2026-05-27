import asyncio
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

import httpx
import websockets

from studyops_core.config import settings


class DeepTutorAdapter:
    def __init__(self, *, base_url: str | None = None, timeout: float = 30.0, cli_enabled: bool | None = None):
        self.base_url = (base_url or settings.deeptutor_base_url).rstrip('/')
        self.timeout = timeout
        self.cli_enabled = settings.deeptutor_cli_enabled if cli_enabled is None else cli_enabled

    def health_check(self) -> dict:
        try:
            response = httpx.get(self._url('/api/v1/knowledge/health'), timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {'status': 'unavailable', **self.error_detail(exc.response)}
        except httpx.HTTPError as exc:
            return {'status': 'unavailable', 'message': str(exc)}

        payload = response.json()
        status = payload.get('status')
        return {'status': 'ok' if status == 'ok' else 'unavailable', 'raw': payload}

    def create_or_get_kb(self, track: dict) -> dict:
        kb_name = self._kb_name(track)
        response = httpx.get(self._url(f'/api/v1/knowledge/{kb_name}'), timeout=self.timeout)
        if response.status_code == 404:
            return {'deeptutor_kb_id': kb_name, 'status': 'missing'}
        response.raise_for_status()
        return {'deeptutor_kb_id': kb_name, 'status': response.json().get('status', 'ready')}

    def create_kb_from_document(self, *, kb_id: str, file_path: str) -> dict:
        with open(file_path, 'rb') as file:
            response = httpx.post(
                self._url('/api/v1/knowledge/create'),
                data={'name': kb_id, 'rag_provider': 'llamaindex'},
                files=[('files', (Path(file_path).name, file, 'application/octet-stream'))],
                timeout=self.timeout,
            )
        response.raise_for_status()
        return response.json()

    def upload_document(self, *, track_id: str, kb_id: str, file_path: str, title: str) -> dict:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(file_path)
        kb = self.create_or_get_kb({'id': track_id})
        if kb['status'] == 'missing':
            result = self.create_kb_from_document(kb_id=kb_id, file_path=file_path)
        else:
            with path.open('rb') as file:
                response = httpx.post(
                    self._url(f'/api/v1/knowledge/{kb_id}/upload'),
                    files=[('files', (title or path.name, file, 'application/octet-stream'))],
                    timeout=self.timeout,
                )
            response.raise_for_status()
            result = response.json()
        return {
            'deeptutor_document_id': (result.get('files') or [path.name])[0],
            'status': 'processing' if result.get('task_id') else 'ready',
            'task_id': result.get('task_id'),
            'raw': result,
        }

    def get_document_progress(self, *, kb_id: str, has_task: bool = True) -> dict:
        response = httpx.get(self._url(f'/api/v1/knowledge/{kb_id}/progress'), timeout=self.timeout)
        response.raise_for_status()
        progress = response.json()
        return {'status': self._normalize_progress_status(progress, has_task=has_task), 'progress': progress}

    def ask_document(self, *, kb_id: str, question: str, language: str) -> dict:
        try:
            return asyncio.run(self.ask_document_ws(kb_id=kb_id, question=question, language=language))
        except Exception:
            return self.ask_document_cli(kb_id=kb_id, question=question, language=language)

    def ask_document_cli(self, *, kb_id: str, question: str, language: str) -> dict:
        output = self._run_cli_json(
            ['deeptutor', 'run', 'chat', question, '--kb', kb_id, '--tool', 'rag', '--language', language, '--format', 'json']
        )
        return self._normalize_answer(output)

    async def ask_document_ws(self, *, kb_id: str, question: str, language: str) -> dict:
        async with websockets.connect(self._ws_url('/api/v1/chat')) as websocket:
            await websocket.send(
                json.dumps(
                    {
                        'message': question,
                        'kb_name': kb_id,
                        'enable_rag': True,
                        'enable_web_search': False,
                        'language': language,
                    }
                )
            )
            answer = ''
            session_id = None
            sources = {'rag': [], 'web': []}
            while True:
                event = json.loads(await websocket.recv())
                event_type = event.get('type')
                if event_type == 'session':
                    session_id = event.get('session_id')
                elif event_type == 'stream':
                    answer += event.get('content') or ''
                elif event_type == 'sources':
                    sources = {'rag': event.get('rag') or [], 'web': event.get('web') or []}
                elif event_type == 'result':
                    answer = event.get('content') or answer
                    break
                elif event_type == 'error':
                    raise RuntimeError(event.get('message') or 'DeepTutor chat failed')
            return {'answer': answer, 'citations': sources.get('rag') or [], 'session_id': session_id, 'raw': {'sources': sources}}

    def generate_quiz(self, payload: dict) -> dict:
        topic = ', '.join(payload.get('topic_tags') or []) or 'general review'
        question_count = payload.get('question_count') or 5
        output = self._run_cli_json(
            [
                'deeptutor',
                'run',
                'deep_question',
                topic,
                '--config',
                f'num_questions={question_count}',
                '--format',
                'json',
            ]
        )
        return {
            'deeptutor_quiz_id': output.get('quiz_id') or output.get('session_id') or 'deeptutor_quiz',
            'questions': output.get('questions') or output.get('items') or [],
            'raw': output,
        }

    def grade_quiz(self, payload: dict) -> dict:
        answers = self._normalize_submitted_answers(payload.get('answers') or [])
        questions = self._normalize_quiz_questions(payload.get('questions') or payload.get('quiz_payload', {}).get('questions') or [])
        questions_by_id = {question['id']: question for question in questions}
        language = self._judge_language(payload.get('language') or 'vi')
        topic_tags = payload.get('topic_tags') or []
        results = []

        for answer in answers:
            question = questions_by_id.get(answer['question_id'], {'id': answer['question_id'], 'topic_tags': topic_tags})
            try:
                feedback = asyncio.run(
                    self.judge_quiz_answer_ws(
                        question=question,
                        user_answer=answer['answer'],
                        language=language,
                    )
                )
                verdict = self._infer_judge_verdict(feedback)
            except Exception as exc:
                feedback = f'DeepTutor quiz judge unavailable: {exc}'
                verdict = 'needs_review'
            results.append(
                {
                    'question_id': answer['question_id'],
                    'verdict': verdict,
                    'score': self._verdict_score(verdict),
                    'feedback': feedback,
                    'topic_tags': question.get('topic_tags') or topic_tags,
                }
            )

        total_count = len(results)
        correct_count = sum(1 for result in results if result['verdict'] == 'correct')
        score = round(sum(result['score'] for result in results) / total_count * 100, 2) if total_count else 0
        mistake_topic_tags = sorted(
            {
                tag
                for result in results
                if result['verdict'] != 'correct'
                for tag in (result.get('topic_tags') or [])
            }
        )
        return {
            'deeptutor_attempt_id': payload.get('deeptutor_quiz_id') or 'deeptutor_attempt',
            'score': score,
            'correct_count': correct_count,
            'total_count': total_count,
            'question_results': results,
            'mistake_topic_tags': mistake_topic_tags,
            'feedback_summary': self._feedback_summary(results),
        }

    async def judge_quiz_answer_ws(self, *, question: dict, user_answer: str, language: str) -> str:
        async with websockets.connect(self._ws_url('/api/v1/question/judge')) as websocket:
            await websocket.send(
                json.dumps(
                    {
                        'question': question.get('question') or '',
                        'question_type': question.get('question_type') or '',
                        'options': question.get('options') or None,
                        'correct_answer': question.get('correct_answer') or '',
                        'explanation': question.get('explanation') or '',
                        'user_answer': user_answer,
                        'language': language,
                    }
                )
            )
            feedback = ''
            while True:
                event = json.loads(await websocket.recv())
                event_type = event.get('type')
                if event_type == 'text':
                    feedback += event.get('content') or ''
                elif event_type == 'done':
                    return feedback.strip()
                elif event_type == 'error':
                    raise RuntimeError(event.get('content') or 'DeepTutor quiz judge failed')


    def _run_cli_json(self, command: list[str]) -> dict:
        if not self.cli_enabled:
            raise RuntimeError('DeepTutor CLI integration is disabled')
        completed = subprocess.run(command, capture_output=True, text=True, check=True, timeout=self.timeout)
        return json.loads(completed.stdout)

    def _url(self, path: str) -> str:
        return f'{self.base_url}/{path.lstrip("/")}'

    def _ws_url(self, path: str) -> str:
        parsed = urlparse(self._url(path))
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        return parsed._replace(scheme=scheme).geturl()

    @staticmethod
    def _normalize_answer(output: dict) -> dict:
        return {
            'answer': output.get('content') or output.get('answer') or output.get('response') or '',
            'citations': output.get('citations') or output.get('sources') or [],
            'session_id': output.get('session_id'),
            'raw': output,
        }

    @staticmethod
    def _normalize_submitted_answers(answers: list[dict] | dict) -> list[dict[str, str]]:
        if isinstance(answers, dict):
            iterable = [{'question_id': key, 'answer': value} for key, value in answers.items()]
        else:
            iterable = answers
        normalized = []
        for index, answer in enumerate(iterable):
            if not isinstance(answer, dict):
                continue
            question_id = answer.get('question_id') or answer.get('id') or answer.get('questionId') or f'q{index + 1}'
            normalized.append({'question_id': str(question_id), 'answer': str(answer.get('answer') or answer.get('value') or '')})
        return normalized

    @staticmethod
    def _normalize_quiz_questions(questions: list[dict]) -> list[dict]:
        normalized = []
        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            question_id = question.get('id') or question.get('question_id') or question.get('questionId') or f'q{index + 1}'
            normalized.append(
                {
                    'id': str(question_id),
                    'question': question.get('question') or question.get('stem') or question.get('prompt') or question.get('text') or '',
                    'question_type': question.get('question_type') or question.get('type') or '',
                    'options': question.get('options') or question.get('choices') or None,
                    'correct_answer': question.get('correct_answer') or question.get('answer') or question.get('correctAnswer') or '',
                    'explanation': question.get('explanation') or question.get('rationale') or question.get('solution') or '',
                    'topic_tags': question.get('topic_tags') or question.get('tags') or [],
                }
            )
        return normalized

    @staticmethod
    def _judge_language(language: str) -> str:
        return 'zh' if language == 'zh' else 'en'

    @staticmethod
    def _infer_judge_verdict(feedback: str) -> str:
        text = feedback.lower()
        if any(marker in text for marker in ['❌', 'incorrect', 'not correct', 'không đúng', 'sai']):
            return 'incorrect'
        if any(marker in text for marker in ['⚠', 'partially correct', 'partial', 'một phần']):
            return 'partial'
        if any(marker in text for marker in ['✅', 'correct', 'đúng']):
            return 'correct'
        return 'needs_review'

    @staticmethod
    def _verdict_score(verdict: str) -> float:
        return {'correct': 1.0, 'partial': 0.5}.get(verdict, 0.0)

    @staticmethod
    def _feedback_summary(results: list[dict]) -> str:
        if not results:
            return 'No answers were submitted.'
        return '\n\n'.join(
            f"{result['question_id']}: {result['verdict']} — {result['feedback']}" for result in results
        )

    @staticmethod
    def _normalize_progress_status(progress: dict, *, has_task: bool) -> str:
        stage = str(progress.get('stage') or '').lower()
        status = str(progress.get('status') or '').lower()
        if stage == 'completed' or status in {'ready', 'success', 'completed'}:
            return 'ready'
        if stage == 'error' or status in {'error', 'failed'}:
            return 'error'
        if status == 'not_started':
            return 'processing' if has_task else 'pending'
        return 'processing'

    @staticmethod
    def _kb_name(track: dict) -> str:
        title = str(track.get('title') or f"track-{track.get('id', 'local')}").lower()
        slug = re.sub(r'[^a-z0-9]+', '-', title).strip('-')
        return f"studyops-{track.get('id', 'local')}-{slug or 'track'}"

    @staticmethod
    def error_detail(response: httpx.Response) -> dict:
        try:
            payload = response.json()
        except ValueError:
            message = response.text
        else:
            message = payload.get('detail') or payload.get('error') or payload.get('message') or str(payload)
        return {'code': response.status_code, 'message': message}
