from fastapi import FastAPI

from api.health import router as health_router
from api.invoke import router as invoke_router
from api.event_init import router as event_init_router
from api.event_novel import router as event_novel_router
from core.config import settings
from core.exceptions import register_exception_handlers
from core.logging import get_logger, setup_logging
from fastapi.middleware.cors import CORSMiddleware

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(invoke_router)
app.include_router(event_init_router)
app.include_router(event_novel_router)


logger.info("FastAPI application initialized")