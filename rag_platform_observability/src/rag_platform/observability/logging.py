import logging
import os
import sys


DEFAULT_LOG_LEVEL = "INFO"


def configure_logging() -> None:
    """
    Configure application-wide logging.

    LOG_LEVEL can be overridden through environment variable:
    INFO, DEBUG, WARNING, ERROR, CRITICAL.
    """

    log_level = os.getenv(
        "LOG_LEVEL",
        DEFAULT_LOG_LEVEL,
    ).upper()

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)