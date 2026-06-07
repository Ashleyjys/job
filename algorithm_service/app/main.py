from fastapi import FastAPI

from app.routers.analysis import router as analysis_router

app = FastAPI(title="Mock Analysis Service")
app.include_router(analysis_router)
