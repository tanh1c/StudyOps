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
