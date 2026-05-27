import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from studyops_core.adapters.ninerouter import NineRouterAdapter

router = APIRouter(prefix='/router', tags=['router'])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float | None = None
    max_tokens: int | None = None


def get_router_adapter():
    return NineRouterAdapter()


@router.get('/models')
def list_router_models():
    try:
        return {'models': get_router_adapter().list_model_groups()}
    except httpx.HTTPStatusError as exc:
        raise_router_error(exc)
    except httpx.HTTPError as exc:
        raise_network_error(exc)


@router.post('/chat/completions')
def create_chat_completion(request: ChatCompletionRequest):
    try:
        return get_router_adapter().create_chat_completion(
            model=request.model,
            messages=[message.model_dump() for message in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except httpx.HTTPStatusError as exc:
        raise_router_error(exc)
    except httpx.HTTPError as exc:
        raise_network_error(exc)


def raise_router_error(exc: httpx.HTTPStatusError):
    raise HTTPException(
        status_code=502,
        detail={'status': 'unavailable', **NineRouterAdapter.error_detail(exc.response)},
    ) from exc


def raise_network_error(exc: httpx.HTTPError):
    raise HTTPException(
        status_code=502,
        detail={'status': 'unavailable', 'message': str(exc)},
    ) from exc
