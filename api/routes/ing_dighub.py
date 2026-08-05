from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backoffice.ing_dighub_platform import IngDighubPlatformService


class ModuleExecuteRequest(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)


class AutonomyRunRequest(BaseModel):
    mission: str = Field(default="ING_DIGHUB Industrial Engineering Platform Evolution")
    context: Dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = Field(default=8, ge=1, le=50)
    min_expected_value: float = Field(default=0.0)


router = APIRouter(prefix="/ing-dighub", tags=["ing-dighub"])
_platform = IngDighubPlatformService()


@router.get("/modules")
def list_modules() -> Dict[str, Any]:
    return {
        "status": "ok",
        "platform": "ING_DIGHUB",
        "modules": _platform.list_modules(),
    }


@router.post("/modules/{module_key}/execute")
def execute_module(module_key: str, payload: ModuleExecuteRequest) -> Dict[str, Any]:
    return _platform.execute_module(module_key, payload.context)


@router.post("/autonomy/run")
def run_autonomy(payload: AutonomyRunRequest) -> Dict[str, Any]:
    return _platform.run_autonomy_loop(
        mission=payload.mission,
        context=payload.context,
        max_iterations=payload.max_iterations,
        min_expected_value=payload.min_expected_value,
    )
