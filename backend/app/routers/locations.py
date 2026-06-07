import httpx
from fastapi import APIRouter, HTTPException, Query

from app.schemas.dashboard import LocationInfo
from app.services.location_service import location_service

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("/search", response_model=list[LocationInfo])
def search_locations(
    q: str = Query(..., min_length=1, description="City keyword"),
    count: int = Query(8, ge=1, le=10, description="Maximum number of candidates"),
) -> list[LocationInfo]:
    try:
        return location_service.search_locations(q, count=count)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Location search upstream unavailable.") from exc
