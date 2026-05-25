from studyops_core.services.policy import classify_action


def test_create_small_task_is_auto():
    decision = classify_action({'type': 'create_small_task'})
    assert decision == 'auto'


def test_modify_active_plan_requires_approval():
    decision = classify_action({'type': 'modify_active_plan'})
    assert decision == 'approval'


def test_shell_command_is_blocked():
    decision = classify_action({'type': 'shell_command'})
    assert decision == 'blocked'
