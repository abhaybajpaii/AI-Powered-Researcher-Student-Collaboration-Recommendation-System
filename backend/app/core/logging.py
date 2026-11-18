import logging
import sys
from backend.app.core.config import settings


def setup_logging():
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","file":"%(filename)s","line":%(lineno)d,"message":"%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%SZ",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json" if settings.ENVIRONMENT == "production" else "standard",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "INFO" if settings.DEBUG else "WARN",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


logger = logging.getLogger("collab_matcher")
