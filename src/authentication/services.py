from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from loguru import logger

from src.common.utils import get_object_or_raise
from src.core.exceptions import ApplicationError, AuthenticationError
from src.users.models import Restaurant


class AuthService:
    def __init__(self, request: HttpRequest):
        self.request = request

    USER_IS_DELETED = _("Restaurant has been deleted.")
    USER_IS_INACTIVE = _("Restaurant account is inactive.")
    INCORRECT_CREDENTIALS = _("Incorrect email or password.")
    USER_NOT_FOUND = _("Restaurant not found.")

    def _verify_user_not_deleted(self, user: Restaurant):
        if user.is_deleted:
            logger.warning(f"Deleted restaurant {user.id} attempted to log in.")
            raise ApplicationError(self.INCORRECT_CREDENTIALS)

    def _verify_user_is_active(self, user: Restaurant):
        if not user.is_active:
            logger.warning(f"Inactive restaurant {user.id} attempted to log in.")
            raise AuthenticationError(self.INCORRECT_CREDENTIALS)

    def login(self, email: str, password: str) -> bool:
        logger.debug(f"Attempting login for email: {email}")

        abstract_user = authenticate(username=email, password=password)

        if not abstract_user:
            logger.warning(f"Failed login attempt for email: {email}")
            raise AuthenticationError(self.INCORRECT_CREDENTIALS)

        user = get_object_or_raise(Restaurant, self.USER_NOT_FOUND, pk=abstract_user.pk)

        self._verify_user_not_deleted(user)
        self._verify_user_is_active(user)

        login(self.request, user)

        return True

    def logout(self) -> None:
        logger.debug(f"Logging out user ID: {self.request.user.pk}")
        logout(self.request)
