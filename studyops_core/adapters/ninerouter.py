from urllib.parse import urljoin

import httpx

from studyops_core.config import settings


class NineRouterAdapter:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 5.0,
    ):
        self.base_url = (base_url or settings.ninerouter_url).rstrip('/')
        self.api_key = api_key if api_key is not None else settings.ninerouter_key
        self.timeout = timeout

    def health_check(self) -> dict:
        try:
            response = httpx.get(
                self._url('/api/health'),
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {
                'status': 'unavailable',
                'code': exc.response.status_code,
                'detail': self._error_detail(exc.response),
            }
        except httpx.HTTPError as exc:
            return {'status': 'unavailable', 'detail': str(exc)}

        payload = response.json()
        return {'status': 'ok' if payload.get('ok') is True else 'unavailable', 'raw': payload}

    def list_models(self) -> dict:
        response = httpx.get(
            self._url('/v1/models'),
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return {'models': payload.get('data', []), 'raw': payload}

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {'Authorization': f'Bearer {self.api_key}'}

    def _url(self, path: str) -> str:
        return urljoin(f'{self.base_url}/', path.lstrip('/'))

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text
        return payload.get('error') or payload.get('message') or str(payload)
