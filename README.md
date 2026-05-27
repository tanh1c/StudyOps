# StudyOps Mentor

Local-first study operating system MVP.

## Run

```bash
cp .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:8000/ui
```

## Local development

```bash
python -m pip install -e ".[dev]"
pytest -v
uvicorn studyops_core.main:app --reload
```

## 9Router integration

StudyOps uses 9Router at `NINEROUTER_URL` for health checks, model discovery, and OpenAI-compatible chat completions.

```bash
NINEROUTER_URL=http://localhost:20128
NINEROUTER_KEY=
NINEROUTER_DEFAULT_CHAT_MODEL=openai/gpt-4o-mini
```

Set `NINEROUTER_KEY` only when 9Router has API-key enforcement enabled. Leave it empty for a local 9Router instance without API-key enforcement.

Implemented 9Router capabilities:

- `GET /api/health` via `/health/services`
- `GET /v1/models` and all documented model groups via `/router/models`
- `POST /v1/chat/completions` via `/router/chat/completions`
- 9Router-backed StudyOps LLM service for mentor flows
- Daily check-in mentor summaries through the 9Router-backed LLM service
- Upstream error mapping for `401`, invalid model errors, and `503` with `retry-after`
