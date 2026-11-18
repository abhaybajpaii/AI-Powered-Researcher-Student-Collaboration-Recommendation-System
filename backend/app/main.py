from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.api import api_router
from backend.app.api.v1.endpoints.health import check_health
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from backend.app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode.")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent academic collaboration matcher connecting students with faculty advisors.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS Middleware
origins = settings.ALLOWED_ORIGINS
if isinstance(origins, str):
    origins = [o.strip() for o in origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Health Endpoint (Direct GET /health as specified)
app.add_api_route(
    "/health",
    check_health,
    methods=["GET"],
    tags=["Health"],
    summary="Root Health Check",
)

# API v1 Router (/api/v1/health, /api/v1/students, /api/v1/faculty)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR,
    }
