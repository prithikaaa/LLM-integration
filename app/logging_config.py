"""Logging setup for the job application automation application."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "job_automation"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3


def configure_logging(
    log_level: str = "INFO",
    log_file: Path | None = None,
) -> logging.Logger:
    """Configure application logging and return the application logger.

    Logs go to the console by default. Set ``log_file`` to also enable a
    rotating UTF-8 log file; parent directories are created when necessary.
    """
    resolved_level = getattr(logging, log_level.upper(), None)
    if not isinstance(resolved_level, int):
        raise ValueError(f"Unsupported log level: {log_level}")

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(resolved_level)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)
    if not any(getattr(handler, "_job_automation_console", False) for handler in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._job_automation_console = True
        logger.addHandler(console_handler)

    if log_file is not None and not any(
        getattr(handler, "baseFilename", None) == str(log_file.resolve())
        for handler in logger.handlers
    ):
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    for handler in logger.handlers:
        handler.setLevel(resolved_level)

    return logger
