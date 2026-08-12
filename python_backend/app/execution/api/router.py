# python_backend/app/execution/api/router.py
"""FastAPI router for Cloud Code Execution Engine (/api/v1/execution).

Endpoints:
  POST /submission/{submission_id} -> Trigger execution pipeline manually (Authority/System)
  GET  /submission/{submission_id} -> Aggregated execution summary & statistics
  GET  /submission/{submission_id}/results -> List test case execution results
  GET  /{execution_id}             -> Get single test execution result detail
  GET  /health                      -> Judge0 provider health check
"""

from typing import List
from fastapi import APIRouter, Depends, status

from app.editor.dependencies import get_current_user_context
from app.execution.dependencies import get_execution_service
from app.execution.schemas.execution import (
    ExecutionHealthResponse,
    ExecutionResultResponse,
    ExecutionStartResponse,
    ExecutionSummaryResponse,
    ExecutionTestCaseResultResponse,
)
from app.execution.services.execution_service import ExecutionService
from app.execution.exceptions import ExecutionAccessDeniedError

router = APIRouter()


@router.get(
    "/health",
    response_model=ExecutionHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Execution provider health check",
    description="Returns Judge0 provider status, configuration state, and availability.",
)
async def get_health(
    service: ExecutionService = Depends(get_execution_service),
) -> ExecutionHealthResponse:
    return await service.get_health()


@router.post(
    "/submission/{submission_id}",
    response_model=ExecutionStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger code execution for a submission",
    description="Manually triggers Judge0 execution for an existing finalized submission. (Authority/System only)",
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Authority role required"},
        404: {"description": "Submission not found"},
    },
)
async def trigger_execution(
    submission_id: int,
    user_ctx: dict = Depends(get_current_user_context),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecutionStartResponse:
    if user_ctx["role"].lower() != "authority":
        raise ExecutionAccessDeniedError()

    # Trigger execution asynchronously
    import asyncio
    asyncio.create_task(service.run_execution_pipeline(submission_id))

    return ExecutionStartResponse(
        submission_id=submission_id,
        status="PROCESSING",
        message="Code execution pipeline started asynchronously.",
    )


@router.get(
    "/submission/{submission_id}",
    response_model=ExecutionSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get submission execution summary",
    description="Returns aggregate execution metrics, pass percentage, runtime, memory, and test case results.",
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Submission not found"},
    },
)
def get_execution_summary(
    submission_id: int,
    user_ctx: dict = Depends(get_current_user_context),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecutionSummaryResponse:
    return service.get_execution_summary(
        submission_id=submission_id,
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
    )


@router.get(
    "/submission/{submission_id}/results",
    response_model=List[ExecutionTestCaseResultResponse],
    status_code=status.HTTP_200_OK,
    summary="List test case execution results",
    description="Returns individual test case outcomes. Hidden test case inputs/outputs are masked for interns.",
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Submission not found"},
    },
)
def list_execution_results(
    submission_id: int,
    user_ctx: dict = Depends(get_current_user_context),
    service: ExecutionService = Depends(get_execution_service),
) -> List[ExecutionTestCaseResultResponse]:
    summary = service.get_execution_summary(
        submission_id=submission_id,
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
    )
    return summary.results


@router.get(
    "/{execution_id}",
    response_model=ExecutionTestCaseResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed single execution result",
    description="Returns detailed outcome for a single test case execution.",
    responses={
        401: {"description": "Unauthenticated"},
        403: {"description": "Access denied"},
        404: {"description": "Execution result not found"},
    },
)
def get_execution_result_detail(
    execution_id: int,
    user_ctx: dict = Depends(get_current_user_context),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecutionTestCaseResultResponse:
    return service.get_result_detail(
        result_id=execution_id,
        current_user_id=user_ctx["user_id"],
        current_user_role=user_ctx["role"],
    )
