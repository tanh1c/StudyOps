from studyops_core.services.llm import chat_with_model, extract_assistant_text


class StubRouterAdapter:
    def __init__(self):
        self.calls = []

    def create_chat_completion(self, *, model, messages, temperature=None, max_tokens=None):
        self.calls.append(
            {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
            }
        )
        return {
            'choices': [
                {
                    'message': {
                        'role': 'assistant',
                        'content': 'Kế hoạch học hôm nay',
                    }
                }
            ]
        }


def test_chat_with_model_uses_default_chat_model():
    adapter = StubRouterAdapter()

    result = chat_with_model(
        messages=[{'role': 'user', 'content': 'Tạo kế hoạch học'}],
        temperature=0.3,
        max_tokens=256,
        router_adapter=adapter,
    )

    assert adapter.calls == [
        {
            'model': 'openai/gpt-4o-mini',
            'messages': [{'role': 'user', 'content': 'Tạo kế hoạch học'}],
            'temperature': 0.3,
            'max_tokens': 256,
        }
    ]
    assert extract_assistant_text(result) == 'Kế hoạch học hôm nay'


def test_chat_with_model_accepts_model_override():
    adapter = StubRouterAdapter()

    chat_with_model(
        model='anthropic/claude-sonnet-4-6',
        messages=[{'role': 'user', 'content': 'Chào'}],
        router_adapter=adapter,
    )

    assert adapter.calls[0]['model'] == 'anthropic/claude-sonnet-4-6'


def test_extract_assistant_text_handles_missing_choices():
    assert extract_assistant_text({}) == ''
