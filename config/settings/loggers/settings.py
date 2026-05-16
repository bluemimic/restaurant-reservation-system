from enum import Enum

from config.env import env, env_to_enum


class LoggingFormat(Enum):
    DEV = "dev"
    PROD = "prod"


LOGGING_FORMAT = env_to_enum(LoggingFormat, env("LOGGING_FORMAT", default=LoggingFormat.DEV.value))


LOG_PATH = env("LOG_PATH", default="logs/app.log")

LOG_LEVEL = env("LOG_LEVEL", default="INFO")
