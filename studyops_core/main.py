from fastapi import FastAPI

app = FastAPI(title='StudyOps Core')


@app.get('/health')
def health():
    return {'status': 'ok'}
