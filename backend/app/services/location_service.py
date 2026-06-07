from __future__ import annotations

from app.config import settings
from app.schemas.dashboard import LocationInfo
from app.services.open_meteo_client import OpenMeteoClient


class LocationService:
    def __init__(self, upstream_client: OpenMeteoClient | None = None) -> None:
        self._upstream_client = upstream_client or OpenMeteoClient(
            geocoding_base_url=settings.geocoding_api_base_url,
            weather_base_url=settings.weather_api_base_url,
            air_quality_base_url=settings.air_quality_api_base_url,
        )

    def search_locations(self, query: str, count: int = 8) -> list[LocationInfo]:
        return self._upstream_client.search_cities(query.strip(), count=count)


location_service = LocationService()
