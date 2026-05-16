import sys

from loguru import logger


class LoggersSetup:
    @staticmethod
    def setup_loguru():
        from config.settings.loggers.settings import LOGGING_FORMAT, LOG_LEVEL, LOG_PATH, LoggingFormat

        logger.remove()

        if LOGGING_FORMAT == LoggingFormat.DEV:
            logger.add(
                sys.stdout,
                level=LOG_LEVEL,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
                "| <level>{level}</level> "
                "| <cyan>{module}</cyan> "
                "| {file}:{line} {function}"
                "| pid={process} tid={thread} "
                "| {message}",
                colorize=True,
            )

        if LOGGING_FORMAT == LoggingFormat.PROD:
            logger.add(
                LOG_PATH,
                level=LOG_LEVEL,
                rotation="10 MB",
                retention="7 days",
                serialize=True,
                encoding="utf-8",
            )
