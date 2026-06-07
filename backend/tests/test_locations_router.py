from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dashboard import LocationInfo

client = TestClient(app)


def test_location_search_returns_candidates(monkeypatch):
    monkeypatch.setattr(
        "app.services.location_service.location_service.search_locations",
        lambda query, count: [
            LocationInfo(
                name="Chengdu",
                country="China",
                admin1="Sichuan",
                latitude=30.66667,
                longitude=104.06667,
                timezone="Asia/Shanghai",
            ),
            LocationInfo(
                name="Chengdu County",
                country="United States",
                admin1="Idaho",
                latitude=43.0,
                longitude=-116.0,
                timezone="America/Boise",
            ),
        ],
    )

    response = client.get("/api/v1/locations/search", params={"q": "cheng", "count": 2})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["name"] == "Chengdu"
    assert body[1]["country"] == "United States"


def test_location_search_validates_blank_query():
    response = client.get("/api/v1/locations/search", params={"q": ""})

    assert response.status_code == 422
