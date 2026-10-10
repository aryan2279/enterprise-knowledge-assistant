
from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.search import router as search_router


app = FastAPI(
    title="Enterprise Knowledge Assistant",
    version="1.0.0",
)


app.include_router(
    health_router,
    prefix="/api",
)

app.include_router(
    auth_router,
    prefix="/api",
)

app.include_router(
    documents_router,
    prefix="/api",
)

app.include_router(
    search_router,
    prefix="/api",
)


@app.get("/")
def root():
    return {
        "message": "Enterprise Knowledge Assistant API",
        "status": "running",
    }
