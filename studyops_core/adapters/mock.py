class MockDeepTutorAdapter:
    def create_or_get_kb(self, track: dict) -> dict:
        return {'deeptutor_kb_id': f"dt_kb_{track['id']}"}

    def upload_document(self, *, track_id: str, kb_id: str, file_path: str, title: str) -> dict:
        return {'deeptutor_document_id': 'dt_doc_mock', 'status': 'ready'}

    def ask_document(self, *, kb_id: str, question: str, language: str) -> dict:
        return {
            'answer': f'Mock answer for: {question}',
            'citations': [
                {
                    'document_id': 'dt_doc_mock',
                    'title': 'Mock Lecture',
                    'page': 1,
                    'snippet': 'Mock citation',
                }
            ],
            'session_id': 'dt_session_mock',
        }

    def generate_quiz(self, payload: dict) -> dict:
        return {
            'deeptutor_quiz_id': 'dt_quiz_mock',
            'questions': [
                {
                    'id': 'q1',
                    'type': 'multiple_choice',
                    'question': 'Mock question?',
                    'choices': ['A', 'B'],
                    'topic_tags': ['support-confidence'],
                }
            ],
        }

    def grade_quiz(self, payload: dict) -> dict:
        return {
            'deeptutor_attempt_id': 'dt_attempt_mock',
            'score': 55,
            'correct_count': 1,
            'total_count': 2,
            'question_results': [],
            'mistake_topic_tags': ['support-confidence'],
            'feedback_summary': 'Mock feedback',
        }


class MockHermesAdapter:
    def run_daily_checkin(self, snapshot: dict) -> dict:
        return {'job_summary': 'Mock daily checkin', 'messages': [], 'proposals': []}

    def run_weekly_review(self, snapshot: dict) -> dict:
        return {
            'job_summary': 'Mock weekly review',
            'observations': [],
            'track_assessments': [],
            'proposals': [],
        }

    def run_plan_rebalance(self, snapshot: dict, instruction: str) -> dict:
        return {'job_summary': f'Mock rebalance: {instruction}', 'proposals': []}


class MockRouterAdapter:
    def health_check(self) -> dict:
        return {'status': 'ok', 'models': ['mock-model']}
