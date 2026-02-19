"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.db.sqlalchemy.session import close_engine, init_engine
from app.presentation.api.middleware.correlation_id import correlation_id_middleware
from app.presentation.api.middleware.error_handler import error_handler_middleware
from app.presentation.api.middleware.rate_limit import rate_limit_middleware
from app.presentation.api.routes.auth_routes import router as auth_router
from app.presentation.api.routes.rbac_routes import router as rbac_router
from app.presentation.api.routes.admin_product_routes import router as admin_product_router
from app.presentation.api.routes.storefront_product_routes import router as storefront_product_router
from app.presentation.api.routes.admin_category_routes import router as admin_category_router
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create FastAPI app
app = FastAPI(
    title="E-Commerce API",
    description="Production-ready e-commerce API with Clean Architecture",
    version="0.1.0",
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(correlation_id_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(error_handler_middleware)

# Include routers
app.include_router(auth_router)
app.include_router(rbac_router)
app.include_router(admin_product_router)
app.include_router(storefront_product_router)
app.include_router(admin_category_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    init_engine(str(settings.database_url))
    logging.info("Database engine initialized")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    await close_engine()
    logging.info("Database engine closed")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.presentation.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
