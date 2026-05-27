from studyops_core.adapters.ninerouter import NineRouterAdapter
from studyops_core.config import settings


def chat_with_model(
    *,
    messages: list[dict],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    router_adapter: NineRouterAdapter | None = None,
) -> dict:
    adapter = router_adapter or NineRouterAdapter()
    return adapter.create_chat_completion(
        model=model or settings.ninerouter_default_chat_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def extract_assistant_text(completion: dict) -> str:
    choices = completion.get('choices') or []
    if not choices:
        return ''
    message = choices[0].get('message') or {}
    return message.get('content') or ''
