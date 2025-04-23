from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import auth, conversions, deploy
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Markdown to HTML static site generator API",
    version="1.0.0",
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(conversions.router, prefix="/api/conversions", tags=["conversions"])
app.include_router(deploy.router, prefix="/api/deploy", tags=["deployment"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")

