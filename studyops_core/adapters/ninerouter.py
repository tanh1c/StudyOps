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
        return self._list_models('/v1/models')

    def list_image_models(self) -> dict:
        return self._list_models('/v1/models/image')

    def list_tts_models(self) -> dict:
        return self._list_models('/v1/models/tts')

    def list_embedding_models(self) -> dict:
        return self._list_models('/v1/models/embedding')

    def list_web_models(self) -> dict:
        return self._list_models('/v1/models/web')

    def list_stt_models(self) -> dict:
        return self._list_models('/v1/models/stt')

    def list_image_to_text_models(self) -> dict:
        return self._list_models('/v1/models/image-to-text')

    def list_model_groups(self) -> dict:
        return {
            'chat': self.list_models()['models'],
            'image': self.list_image_models()['models'],
            'tts': self.list_tts_models()['models'],
            'embedding': self.list_embedding_models()['models'],
            'web': self.list_web_models()['models'],
            'stt': self.list_stt_models()['models'],
            'image_to_text': self.list_image_to_text_models()['models'],
        }

    def _list_models(self, path: str) -> dict:
        response = httpx.get(
            self._url(path),
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
