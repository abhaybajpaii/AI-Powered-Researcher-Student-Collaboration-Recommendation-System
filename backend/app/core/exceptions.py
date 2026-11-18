from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorParam(BaseModel):
    field: str
    message: str
    value: Optional[Any] = None


class ProblemDetails(BaseModel):
    type: str = Field(default="about:blank")
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    code: str
    invalid_params: List[ErrorParam] = Field(default_factory=list)


class AppException(Exception):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        title: str = "Internal Server Error",
        detail: str = "An unexpected error occurred.",
        code: str = "INTERNAL_ERROR",
        error_type: str = "https://api.collab-matcher.edu/errors/internal-error",
        invalid_params: Optional[List[ErrorParam]] = None,
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.code = code
        self.error_type = error_type
        self.invalid_params = invalid_params or []
        super().__init__(detail)


class EntityNotFoundException(AppException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Resource Not Found",
            detail=f"{entity_name} with identifier '{identifier}' was not found.",
            code=f"{entity_name.upper()}_NOT_FOUND",
            error_type="https://api.collab-matcher.edu/errors/not-found",
        )


class EntityConflictException(AppException):
    def __init__(self, detail: str, code: str = "RESOURCE_CONFLICT"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            title="Resource Conflict",
            detail=detail,
            code=code,
            error_type="https://api.collab-matcher.edu/errors/conflict",
        )


class ValidationException(AppException):
    def __init__(self, detail: str, invalid_params: Optional[List[ErrorParam]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation Error",
            detail=detail,
            code="VALIDATION_ERROR",
            error_type="https://api.collab-matcher.edu/errors/validation-error",
            invalid_params=invalid_params or [],
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    problem = ProblemDetails(
        type=exc.error_type,
        title=exc.title,
        status=exc.status_code,
        detail=exc.detail,
        instance=str(request.url.path),
        code=exc.code,
        invalid_params=exc.invalid_params,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    invalid_params = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", []) if p != "body")
        invalid_params.append(
            ErrorParam(
                field=loc or "body",
                message=err.get("msg", "Invalid value"),
                value=err.get("input"),
            )
        )

    problem = ProblemDetails(
        type="https://api.collab-matcher.edu/errors/validation-error",
        title="Request Validation Failed",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="One or more fields in the request body or parameters failed validation.",
        instance=str(request.url.path),
        code="REQUEST_VALIDATION_FAILED",
        invalid_params=invalid_params,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    problem = ProblemDetails(
        type="https://api.collab-matcher.edu/errors/internal-server-error",
        title="Internal Server Error",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected internal error occurred. Please contact the administrator.",
        instance=str(request.url.path),
        code="INTERNAL_SERVER_ERROR",
        invalid_params=[],
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )
