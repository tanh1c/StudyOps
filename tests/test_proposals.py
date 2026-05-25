from sqlmodel import Session, select

from studyops_core.models import AgentProposal, ApprovalRequest
from studyops_core.services.proposals import create_proposal_with_policy


def test_medium_risk_proposal_creates_approval(session: Session):
    proposal = create_proposal_with_policy(
        session=session,
        user_id='usr_local',
        proposal_type='modify_plan',
        title='Rebalance week',
        summary='Move project task later',
        rationale='Midterm is near',
        proposed_changes={'actions': [{'type': 'modify_active_plan'}]},
    )

    approval = session.exec(select(ApprovalRequest).where(ApprovalRequest.proposal_id == proposal.id)).one()
    assert proposal.status == 'pending'
    assert approval.status == 'pending'
