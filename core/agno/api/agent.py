from core.agno.api.api import api
from core.agno.api.routes import ApiRoutes
from core.agno.api.schemas.agent import AgentRunCreate
from core.agno.utils.log import log_debug


def create_agent_run(run: AgentRunCreate) -> None:
    """Telemetry recording for Agent runs"""
    with api.Client() as api_client:
        try:
            api_client.post(
                ApiRoutes.RUN_CREATE,
                json=run.model_dump(exclude_none=True),
            )
        except Exception as e:
            log_debug(f"Could not create Agent run: {e}")


async def acreate_agent_run(run: AgentRunCreate) -> None:
    """Telemetry recording for async Agent runs"""
    async with api.AsyncClient() as api_client:
        try:
            await api_client.post(
                ApiRoutes.RUN_CREATE,
                json=run.model_dump(exclude_none=True),
            )
        except Exception as e:
            log_debug(f"Could not create Agent run: {e}")
