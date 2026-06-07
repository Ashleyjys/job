from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.analysis import router as analysis_router
from app.routers.dashboard import router as dashboard_router
from app.routers.health import router as health_router
from app.routers.locations import router as locations_router

app = FastAPI(title="Air Quality Weather Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(analysis_router)
app.include_router(dashboard_router)
app.include_router(locations_router)
