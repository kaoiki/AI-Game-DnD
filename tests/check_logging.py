from core.logging import get_logger

logger = get_logger(__name__)

logger.debug("this is a debug log")
logger.info("this is an info log")
logger.warning("this is a warning log")
logger.error("this is an error log")