from core.exceptions import AppException
from core.logging import get_logger

logger = get_logger(__name__)

try:
    logger.info("start exception test")

    raise AppException(message="test app exception", code=4001)

except AppException as e:
    logger.warning("AppException caught")

    print("message:", e.message)
    print("code:", e.code)