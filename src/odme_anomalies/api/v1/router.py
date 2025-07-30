from fastapi import APIRouter
from .endpoints.ingest import router as ingest_router
from .endpoints.anomalies import router as anomalies_router
from .endpoints.resolve import router as resolve_router
from .endpoints.report import router as report_router

router = APIRouter()

router.include_router(ingest_router)
router.include_router(anomalies_router)
router.include_router(resolve_router, tags=["Resolve"])
router.include_router(report_router, tags=["Reports"])
