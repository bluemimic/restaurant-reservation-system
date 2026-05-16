from django.utils.translation import gettext_lazy as _


class DomainError(Exception):
    def __init__(self, message: str, extra=None):
        super().__init__(message)

        self.message = message
        self.extra = extra or {}


class ApplicationError(DomainError):
    def __init__(self, message: str, extra=None):
        super().__init__(message, extra)


class PermissionViolationError(ApplicationError):
    def __init__(self, extra=None):
        super().__init__(_("You do not have permission to perform this action."), extra)


class NotFoundError(DomainError):
    def __init__(self, message: str, extra=None):
        super().__init__(message, extra)


class AuthenticationError(ApplicationError):
    def __init__(self, message: str = _("Authentication failed."), extra=None):
        super().__init__(message, extra)
