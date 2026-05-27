from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse

from studyops_core.db import create_db_and_tables
from studyops_core.routers import autonomy, health, knowledge, profile, quizzes, tasks, tracks


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title='StudyOps Core', lifespan=lifespan)
app.include_router(autonomy.router)
app.include_router(health.router)
app.include_router(knowledge.router)
app.include_router(profile.router)
app.include_router(quizzes.router)
app.include_router(tasks.router)
app.include_router(tracks.router)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/ui')
def web_shell():
    return FileResponse('studyops_core/static/index.html')
