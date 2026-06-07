from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    api_base_url: str = "http://localhost:8000"
    algorithm_service_base_url: str = "http://localhost:8100"
    algorithm_service_timeout_ms: int = 2000
    workflow_id: str = "main"
    weather_api_base_url: str = "https://api.open-meteo.com"
    air_quality_api_base_url: str = "https://air-quality-api.open-meteo.com"
    geocoding_api_base_url: str = "https://geocoding-api.open-meteo.com"
    nixtla_api_base_url: str = "https://api.nixtla.io"
    nixtla_api_key: str | None = None
    nixtla_timeout_ms: int = 4000
    enable_mock_fallback: bool = True
    cors_allow_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:4173,"
        "http://127.0.0.1:4173"
    )

    @property
    def cors_allow_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


settings = Settings()
