from fastapi import FastAPI

from studyops_core.db import create_db_and_tables
from studyops_core.routers import profile, tracks

app = FastAPI(title='StudyOps Core')
app.include_router(profile.router)
app.include_router(tracks.router)


@app.on_event('startup')
def on_startup():
    create_db_and_tables()


@app.get('/health')
def health():
    return {'status': 'ok'}
