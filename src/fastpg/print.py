"""Logging helpers used throughout the package."""

import logging

logger = logging.getLogger(__name__)


def print_red(val: str) -> None:
    """Log an error message.

    Parameters
    ----------
    val: str
        Message to log.
    """

    logger.error(val)


def print_green(val: str) -> None:
    """Log an informational message.

    Parameters
    ----------
    val: str
        Message to log.
    """

    logger.info(val)


def print_yellow(val: str) -> None:
    """Log a warning message.

    Parameters
    ----------
    val: str
        Message to log.
    """

    logger.warning(val)

