from scripts.seed_demo import build_demo_payload


def test_demo_payload_contains_three_tracks():
    payload = build_demo_payload()
    assert len(payload['tracks']) == 3
    assert {track['type'] for track in payload['tracks']} == {'course', 'project', 'career'}
