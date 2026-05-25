from fastapi.testclient import TestClient

from studyops_core.main import app


def test_web_shell_serves_index():
    client = TestClient(app)
    response = client.get('/ui')

    assert response.status_code == 200
    assert 'StudyOps Mentor' in response.text
