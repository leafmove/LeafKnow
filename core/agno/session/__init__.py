from typing import Union

from core.agno.session.agent import AgentSession
from core.agno.session.summary import SessionSummaryManager
from core.agno.session.team import TeamSession
from core.agno.session.workflow import WorkflowSession

Session = Union[AgentSession, TeamSession, WorkflowSession]

__all__ = ["AgentSession", "TeamSession", "WorkflowSession", "Session", "SessionSummaryManager"]
