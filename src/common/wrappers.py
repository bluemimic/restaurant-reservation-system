from django.core.exceptions import ValidationError
from django.db import IntegrityError

from src.common.utils import _is_unique_error
from src.core.exceptions import ApplicationError


def handle_unique_error(message: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except IntegrityError:
                raise ApplicationError(message.format(**kwargs))
            except ValidationError as e:
                if _is_unique_error(e):
                    raise ApplicationError(message.format(**kwargs))
                raise

        return wrapper

    return decorator
