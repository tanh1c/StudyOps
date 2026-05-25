AUTO_ACTIONS = {
    'create_small_task',
    'create_practice_quiz',
    'update_weak_topic_evidence',
    'send_in_app_notification',
    'summarize_progress',
}

APPROVAL_ACTIONS = {
    'modify_active_plan',
    'reschedule_many_tasks',
    'adjust_track_priority',
    'mark_goal_at_risk',
    'replace_weekly_plan',
    'drop_task',
}

BLOCKED_ACTIONS = {
    'delete_data',
    'external_message',
    'submit_assignment',
    'shell_command',
    'external_account_action',
}


def classify_action(action: dict) -> str:
    action_type = action['type']
    if action_type in BLOCKED_ACTIONS:
        return 'blocked'
    if action_type in APPROVAL_ACTIONS:
        return 'approval'
    if action_type in AUTO_ACTIONS:
        return 'auto'
    return 'approval'
