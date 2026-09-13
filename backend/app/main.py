"""
SIH26165 — FastAPI Application Entrypoint
Phase 9.1 — Production Backend API
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.app.core.config import settings
from backend.app.db.database import init_db
from backend.app.api.routes import health, reports, dashboard, auth

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sif_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema upon application startup."""
    logger.info("Initializing relational database tables...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.error(f"Database initialization error: {exc}", exc_info=True)
    yield
    logger.info("Shutting down SIF backend service.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production REST API for Serious Injury & Fatality (SIF) Precursor Detection. "
        "Consumes the frozen V2.3 deterministic rule engine and Phase 6.1 TF-IDF ML baseline."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers (Protecting against internal trace leakage)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Returns clean 422 validation error messages."""
    clean_errors = []
    for err in exc.errors():
        clean_errors.append({
            "type": str(err.get("type")),
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": str(err.get("msg")),
            "input": str(err.get("input", ""))
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": clean_errors
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Logs internal error and returns user-friendly 500 response without stack trace."""
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred while processing the request. Please try again later."
        }
    )


# Include API Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root():
    """Root redirect to OpenAPI documentation."""
    return {
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "status": "online"
    }
