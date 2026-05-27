from fastapi.testclient import TestClient

from studyops_core.main import app
from studyops_core.routers import quizzes


class StubDeepTutorAdapter:
    def generate_quiz(self, payload):
        return {'deeptutor_quiz_id': 'dt_quiz_mock', 'questions': [{'id': 'q1'}]}

    def grade_quiz(self, payload):
        return {
            'deeptutor_attempt_id': 'dt_attempt_mock',
            'score': 55,
            'correct_count': 1,
            'total_count': 2,
            'question_results': [],
            'mistake_topic_tags': ['apriori'],
            'feedback_summary': 'Feedback',
        }


def test_generate_and_attempt_quiz_updates_weak_topic(client_session, monkeypatch):
    monkeypatch.setattr(quizzes, 'get_deeptutor_adapter', lambda: StubDeepTutorAdapter())
    client = TestClient(app)
    track = client.post('/tracks', json={'user_id': 'usr_local', 'type': 'course', 'title': 'Data Mining'}).json()
    quiz_response = client.post(f"/tracks/{track['id']}/quizzes/generate", json={
        'knowledge_item_ids': [],
        'topic_tags': ['apriori'],
        'difficulty': 'medium',
        'question_count': 2,
        'language': 'vi',
    })
    assert quiz_response.status_code == 200
    quiz = quiz_response.json()

    attempt_response = client.post(f"/quizzes/{quiz['id']}/attempts", json={'answers': [{'question_id': 'q1', 'answer': 'B'}]})
    assert attempt_response.status_code == 200
    attempt = attempt_response.json()
    assert attempt['score'] == 55
    assert attempt['weak_topics_updated']
