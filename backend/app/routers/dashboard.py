from fastapi import APIRouter

from app.schemas.dashboard import DashboardQueryRequest, DashboardViewModel
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.post("/query", response_model=DashboardViewModel)
def query_dashboard(payload: DashboardQueryRequest) -> DashboardViewModel:
    return dashboard_service.query_dashboard(payload)
