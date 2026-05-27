class MockDeepTutorAdapter:
    def health_check(self) -> dict:
        return {'status': 'ok'}

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
            'job_summary': 'Data Mining needs priority this week.',
            'observations': [],
            'track_assessments': [],
            'proposals': [
                {
                    'proposal_type': 'modify_plan',
                    'title': 'Prioritize Data Mining this week',
                    'summary': 'Move one project task later and add Data Mining review.',
                    'rationale': 'Midterm is close and quiz score is low.',
                    'evidence_event_ids': [],
                    'proposed_changes': {'actions': [{'type': 'modify_active_plan'}]},
                }
            ],
        }

    def run_plan_rebalance(self, snapshot: dict, instruction: str) -> dict:
        return {'job_summary': f'Mock rebalance: {instruction}', 'proposals': []}


class MockRouterAdapter:
    def health_check(self) -> dict:
        return {'status': 'ok', 'models': ['mock-model']}

    def list_models(self) -> dict:
        return {'models': [{'id': 'mock-model'}]}

    def list_model_groups(self) -> dict:
        return {
            'chat': [{'id': 'mock-model'}],
            'image': [],
            'tts': [],
            'embedding': [],
            'web': [],
            'stt': [],
            'image_to_text': [],
        }

    def create_chat_completion(
        self,
        *,
        model: str,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        return {
            'id': 'chatcmpl_mock',
            'model': model,
            'choices': [
                {
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': f"Mock response to: {messages[-1]['content']}",
                    },
                    'finish_reason': 'stop',
                }
            ],
        }
