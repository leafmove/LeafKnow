from typing import List, Optional

from fastapi.routing import APIRouter

from core.agno.agent import Agent
from core.agno.os.interfaces.base import BaseInterface
from core.agno.os.interfaces.whatsapp.router import attach_routes
from core.agno.team import Team


class Whatsapp(BaseInterface):
    type = "whatsapp"

    router: APIRouter

    def __init__(
        self,
        agent: Optional[Agent] = None,
        team: Optional[Team] = None,
        prefix: str = "/whatsapp",
        tags: Optional[List[str]] = None,
    ):
        self.agent = agent
        self.team = team
        self.prefix = prefix
        self.tags = tags or ["Whatsapp"]

        if not (self.agent or self.team):
            raise ValueError("Whatsapp requires an agent or a team")

    def get_router(self) -> APIRouter:
        self.router = APIRouter(prefix=self.prefix, tags=self.tags)  # type: ignore

        self.router = attach_routes(router=self.router, agent=self.agent, team=self.team)

        return self.router
