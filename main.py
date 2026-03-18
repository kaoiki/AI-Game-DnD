from fastapi import FastAPI

from api.health import router as health_router
from api.invoke import router as invoke_router
from core.config import settings
from core.exceptions import register_exception_handlers
from core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(invoke_router)


logger.info("FastAPI application initialized")