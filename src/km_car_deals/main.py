"""KM Car Deals AI Agent - FastAPI application assembly."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from km_car_deals.core.config import settings
from km_car_deals.core.logging import setup_logging
from km_car_deals.api.routes import customers, intake, ops, public, vehicles
from km_car_deals.api.webhooks import whatsapp

setup_logging(settings.LOG_LEVEL, json_output=settings.APP_ENV == "production")

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True if settings.cors_origin_list != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router, prefix=settings.API_PREFIX)
app.include_router(vehicles.router, prefix=settings.API_PREFIX)
app.include_router(intake.router, prefix=settings.API_PREFIX)
app.include_router(customers.router, prefix=settings.API_PREFIX)
app.include_router(ops.router, prefix=settings.API_PREFIX)

# Webhooks root (no /api/v1 prefix)
app.include_router(whatsapp.router)


# ---- Static dashboard + uploaded media serving ----
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Uploaded vehicle photos / exports (never committed to git)
_UPLOAD_DIR = Path(settings.UPLOAD_DIR).resolve()
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")


@app.get("/")
def root():
    from fastapi.responses import FileResponse

    index = _STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"service": settings.APP_NAME, "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
