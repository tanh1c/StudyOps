def build_demo_payload():
    return {
        'profile': {
            'display_name': 'Demo Student',
            'education_level': 'university',
            'major': 'Computer Science',
        },
        'tracks': [
            {'type': 'course', 'title': 'Data Mining', 'priority': 'high'},
            {'type': 'project', 'title': 'Portfolio RAG Chatbot', 'priority': 'medium'},
            {'type': 'career', 'title': 'AI Engineer Internship', 'priority': 'high'},
        ],
    }


if __name__ == '__main__':
    print(build_demo_payload())
