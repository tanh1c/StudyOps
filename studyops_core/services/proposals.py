from sqlmodel import Session

from studyops_core.models import AgentProposal, ApprovalRequest
from studyops_core.services.events import record_event
from studyops_core.services.policy import classify_action


def create_proposal_with_policy(
    *,
    session: Session,
    user_id: str,
    proposal_type: str,
    title: str,
    summary: str,
    rationale: str,
    proposed_changes: dict,
    evidence_event_ids: list[int] | None = None,
) -> AgentProposal:
    actions = proposed_changes.get('actions', [])
    decisions = [classify_action(action) for action in actions] or ['approval']

    if 'blocked' in decisions:
        status = 'rejected'
        risk_level = 'high'
    elif 'approval' in decisions:
        status = 'pending'
        risk_level = 'medium'
    else:
        status = 'auto_applied'
        risk_level = 'low'

    proposal = AgentProposal(
        user_id=user_id,
        proposal_type=proposal_type,
        title=title,
        summary=summary,
        rationale=rationale,
        evidence_event_ids=evidence_event_ids or [],
        proposed_changes=proposed_changes,
        risk_level=risk_level,
        status=status,
    )
    session.add(proposal)
    session.commit()
    session.refresh(proposal)

    if status == 'pending':
        approval = ApprovalRequest(proposal_id=proposal.id or 0, user_id=user_id, required_for=proposal_type)
        session.add(approval)
        session.commit()

    record_event(
        session,
        event_type='agent_proposal.created',
        actor='hermes',
        payload={'user_id': user_id, 'proposal_id': proposal.id, 'status': status},
    )
    return proposal
