import asyncio
import json
import re
from urllib.parse import urlparse

import websockets

from studyops_core.config import settings


class HermesAdapter:
    def __init__(self, *, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.hermes_base_url).rstrip('/')
        self.timeout = timeout or settings.hermes_timeout_seconds

    def health_check(self) -> dict:
        try:
            return asyncio.run(self._health_check_ws())
        except Exception as exc:
            return {'status': 'unavailable', 'message': str(exc)}

    def run_daily_checkin(self, snapshot: dict) -> dict:
        return asyncio.run(
            self._run_prompt(
                self._daily_checkin_prompt(snapshot),
                expected_keys=['job_summary', 'messages', 'proposals'],
            )
        )

    def run_weekly_review(self, snapshot: dict) -> dict:
        return asyncio.run(
            self._run_prompt(
                self._weekly_review_prompt(snapshot),
                expected_keys=['job_summary', 'observations', 'track_assessments', 'proposals'],
            )
        )

    def run_plan_rebalance(self, snapshot: dict, instruction: str) -> dict:
        return asyncio.run(
            self._run_prompt(
                self._plan_rebalance_prompt(snapshot, instruction),
                expected_keys=['job_summary', 'proposals'],
            )
        )

    async def _health_check_ws(self) -> dict:
        async with websockets.connect(self._ws_url('/api/ws')) as websocket:
            event = await asyncio.wait_for(websocket.recv(), timeout=self.timeout)
            payload = json.loads(event)
            event_type = payload.get('params', {}).get('type') or payload.get('type')
            if event_type != 'gateway.ready':
                return {'status': 'unavailable', 'raw': payload}
            return {'status': 'ok', 'raw': payload}

    async def _run_prompt(self, prompt: str, *, expected_keys: list[str]) -> dict:
        async with websockets.connect(self._ws_url('/api/ws')) as websocket:
            ready = json.loads(await asyncio.wait_for(websocket.recv(), timeout=self.timeout))
            session_response = await self._send_rpc(websocket, 1, 'session.create', {})
            session_id = session_response['result']['session_id']
            await self._send_rpc(websocket, 2, 'prompt.submit', {'session_id': session_id, 'prompt': prompt})
            content = await self._wait_for_message_complete(websocket)
            await self._send_rpc(websocket, 3, 'session.close', {'session_id': session_id})
            return self._normalize_output(content, expected_keys=expected_keys, raw={'ready': ready})

    async def _send_rpc(self, websocket, request_id: int, method: str, params: dict) -> dict:
        await websocket.send(json.dumps({'jsonrpc': '2.0', 'id': request_id, 'method': method, 'params': params}))
        while True:
            message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=self.timeout))
            if message.get('id') != request_id:
                continue
            if message.get('error'):
                error = message['error']
                raise RuntimeError(error.get('message') or str(error))
            return message

    async def _wait_for_message_complete(self, websocket) -> str:
        chunks = []
        while True:
            message = json.loads(await asyncio.wait_for(websocket.recv(), timeout=self.timeout))
            if message.get('error'):
                error = message['error']
                raise RuntimeError(error.get('message') or str(error))
            params = message.get('params') or {}
            event_type = params.get('type') or message.get('type')
            payload = params.get('payload') or message.get('payload') or {}
            if event_type == 'message.delta':
                chunks.append(str(payload.get('content') or payload.get('delta') or payload.get('text') or ''))
            elif event_type == 'message.complete':
                return str(payload.get('content') or payload.get('text') or ''.join(chunks))
            elif event_type == 'error':
                raise RuntimeError(payload.get('message') or 'Hermes prompt failed')

    def _ws_url(self, path: str = '/api/ws') -> str:
        parsed = urlparse(f'{self.base_url}/{path.lstrip("/")}')
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        return parsed._replace(scheme=scheme).geturl()

    @classmethod
    def _normalize_output(cls, content: str, *, expected_keys: list[str], raw: dict | None = None) -> dict:
        parsed = cls._parse_json(content)
        if not isinstance(parsed, dict):
            return {'job_summary': content.strip(), 'messages': [], 'proposals': [], 'raw': raw or {'content': content}}

        normalized = {key: parsed.get(key) for key in expected_keys if key in parsed}
        normalized['job_summary'] = str(parsed.get('job_summary') or parsed.get('summary') or '').strip()
        normalized['messages'] = parsed.get('messages') or []
        normalized['proposals'] = [cls._normalize_proposal(proposal) for proposal in parsed.get('proposals') or []]
        normalized['raw'] = parsed
        return normalized

    @staticmethod
    def _parse_json(content: str):
        text = content.strip()
        if not text:
            return None
        fenced = re.search(r'```(?:json)?\s*(.*?)```', text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            text = fenced.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _normalize_proposal(proposal: dict) -> dict:
        proposed_changes = proposal.get('proposed_changes') or proposal.get('changes') or {}
        return {
            'proposal_type': proposal.get('proposal_type') or proposal.get('type') or 'modify_plan',
            'title': proposal.get('title') or 'Hermes proposal',
            'summary': proposal.get('summary') or proposal.get('description') or '',
            'rationale': proposal.get('rationale') or proposal.get('reason') or '',
            'evidence_event_ids': proposal.get('evidence_event_ids') or [],
            'proposed_changes': proposed_changes if isinstance(proposed_changes, dict) else {'changes': proposed_changes},
        }

    @staticmethod
    def _json_block(snapshot: dict) -> str:
        return json.dumps(snapshot, ensure_ascii=False, default=str)

    def _daily_checkin_prompt(self, snapshot: dict) -> str:
        return (
            'Bạn là StudyOps Mentor. Hãy tạo daily check-in bằng tiếng Việt từ snapshot sau. '
            'Chỉ trả về JSON hợp lệ với keys: job_summary, messages, proposals. '
            'Không tự thực thi hành động; nếu cần thay đổi kế hoạch, chỉ tạo proposals.\n'
            f'{self._json_block(snapshot)}'
        )

    def _weekly_review_prompt(self, snapshot: dict) -> str:
        return (
            'Bạn là StudyOps Mentor. Hãy tạo weekly review bằng tiếng Việt từ snapshot sau. '
            'Chỉ trả về JSON hợp lệ với keys: job_summary, observations, track_assessments, proposals. '
            'Mọi thay đổi kế hoạch phải nằm trong proposals để StudyOps xin phê duyệt.\n'
            f'{self._json_block(snapshot)}'
        )

    def _plan_rebalance_prompt(self, snapshot: dict, instruction: str) -> str:
        return (
            'Bạn là StudyOps Mentor. Hãy đề xuất cân bằng lại kế hoạch học bằng tiếng Việt. '
            'Chỉ trả về JSON hợp lệ với keys: job_summary, proposals. '
            'Không tự áp dụng thay đổi.\n'
            f'Instruction: {instruction}\nSnapshot: {self._json_block(snapshot)}'
        )
