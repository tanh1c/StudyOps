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

StudyOps checks 9Router at `NINEROUTER_URL` using the upstream health endpoint `/api/health` and model endpoint `/v1/models`.

```bash
NINEROUTER_URL=http://localhost:20128
NINEROUTER_KEY=
```

Set `NINEROUTER_KEY` only when 9Router has API-key enforcement enabled. Leave it empty for a local 9Router instance without API-key enforcement.
