from fastapi.testclient import TestClient

from studyops_core.main import app


def test_create_or_update_profile(client_session):
    client = TestClient(app)
    response = client.put('/profile', json={
        'display_name': 'Long',
        'education_level': 'university',
        'major': 'Computer Science',
        'semester': 'Year 3',
        'timezone': 'Asia/Ho_Chi_Minh',
    })

    assert response.status_code == 200
    data = response.json()
    assert data['display_name'] == 'Long'
    assert data['major'] == 'Computer Science'
