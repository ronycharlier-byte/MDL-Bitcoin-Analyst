import logging
from logging.handlers import RotatingFileHandler

from config import LOG_PATH, ensure_directories


def setup_logger(name: str = "quant_btc_model") -> logging.Logger:
    ensure_directories()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def log_missing(logger: logging.Logger, field: str, source: str = "unknown") -> None:
    logger.warning("missing_data | field=%s | source=%s | statut=missing", field, source)


def log_mock(logger: logging.Logger, subject: str, reason: str) -> None:
    logger.warning("mock_data | subject=%s | reason=%s | tag=MOCK", subject, reason)
