from fastapi import APIRouter

from app.endpoints.certificate_endpoints import router as certificates_router

api_router = APIRouter()
api_router.include_router(certificates_router)