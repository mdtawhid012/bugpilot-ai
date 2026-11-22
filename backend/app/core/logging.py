import logging


def log_internal_failure(logger: logging.Logger, message: str, request_id: str, error: Exception) -> None:
    logger.error(
        message,
        extra={"request_id": request_id, "exception_type": type(error).__name__},
    )