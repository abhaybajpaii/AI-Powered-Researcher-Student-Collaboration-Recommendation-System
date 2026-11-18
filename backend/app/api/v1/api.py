from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    admin,
    auth,
    embeddings,
    evaluation,
    faculty,
    health,
    recommendations,
    scholarly,
    students,
    taxonomy,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(faculty.router, prefix="/faculty", tags=["Faculty"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Data Pipeline"])
api_router.include_router(scholarly.router, prefix="/scholarly", tags=["Real Research Data & Verification"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["Embeddings"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation"])
api_router.include_router(taxonomy.router, prefix="/taxonomy", tags=["Taxonomy"])
