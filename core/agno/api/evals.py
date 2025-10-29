from core.agno.api.api import api
from core.agno.api.routes import ApiRoutes
from core.agno.api.schemas.evals import EvalRunCreate
from core.agno.utils.log import log_debug


def create_eval_run_telemetry(eval_run: EvalRunCreate) -> None:
    """Telemetry recording for Eval runs"""
    with api.Client() as api_client:
        try:
            api_client.post(ApiRoutes.EVAL_RUN_CREATE, json=eval_run.model_dump(exclude_none=True))
        except Exception as e:
            log_debug(f"Could not create evaluation run: {e}")


async def async_create_eval_run_telemetry(eval_run: EvalRunCreate) -> None:
    """Telemetry recording for async Eval runs"""
    async with api.AsyncClient() as api_client:
        try:
            await api_client.post(ApiRoutes.EVAL_RUN_CREATE, json=eval_run.model_dump(exclude_none=True))
        except Exception as e:
            log_debug(f"Could not create evaluation run: {e}")
