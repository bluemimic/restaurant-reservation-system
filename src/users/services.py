import datetime
import random
from uuid import UUID

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from loguru import logger
from rolepermissions.checkers import has_role
from rolepermissions.roles import assign_role

from promise_tracker.common.services import BaseService
from promise_tracker.common.utils import (
    generate_random_email,
    generate_randon_string,
    get_object_or_raise,
)
from promise_tracker.common.wrappers import handle_unique_error
from promise_tracker.core.exceptions import ApplicationError, EmailDelayError, NotFoundError, PermissionViolationError
from promise_tracker.core.roles import Administrator, RegisteredUser
from promise_tracker.emails.tasks import email_send_task

from .enums import ModerationAction
from .models import BaseUser


class UserService:
    def __init__(
        self,
        performed_by: BaseUser,
        base_service: BaseService[BaseUser] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[BaseUser] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("User not found.")
    UNIQUE_CONSTRAINT_MESSAGE = _("A user with this email already exists.")
    PASSWORDS_DONT_MATCH = _("Passwords do not match.")
    USER_NOT_FOUND = _("User not found.")
    USER_IS_ALREADY_VERIFIED = _("User is already verified.")
    VERIFICATION_FAILED = _("Verification failed! Invalid code!")
    USER_IS_ALREADY_BANNED = _("User is already banned.")
    USER_IS_NOT_BANNED = _("User is not banned.")
    PASSWORD_IS_INVALID = _(
        "Your password must contain at least one digit, one uppercase letter, and one special character."
    )

    def _generate_verification_code(self) -> str:
        digits = "0123456789"
        verification_code = ""

        for i in range(settings.VERIFICATION_CODE_LENGTH):
            verification_code += digits[random.randint(0, len(digits) - 1)]

        return verification_code

    def _generate_verification_code_expiry(self) -> datetime.datetime:
        return timezone.now() + datetime.timedelta(minutes=settings.VERIFICATION_CODE_EXPIRY_MINUTES)

    def _handle_verification(self, user: BaseUser) -> None:
        verification_code = self._generate_verification_code()
        verification_code_expires_at = self._generate_verification_code_expiry()
        user.set_verification_code(verification_code, verification_code_expires_at)

        user.verification_email_sent_at = timezone.now()

        email_send_task.delay(user.email, verification_code)

    def _assign_role(self, user: BaseUser, is_admin: bool) -> None:
        if is_admin:
            logger.debug(f"Assigning Administrator role to user ID {user.id}")
            assign_role(user, Administrator)
        else:
            logger.debug(f"Assigning RegisteredUser role to user ID {user.id}")
            assign_role(user, RegisteredUser)

    def _check_permission_to_create_admin(self, is_admin: bool) -> None:
        if is_admin and not has_role(self.performed_by, Administrator):
            logger.error(f"User {self.performed_by.id} attempted to create an admin user without permission.")
            raise PermissionViolationError()

    def _check_is_owner_or_admin(self, user: BaseUser) -> None:
        if not has_role(self.performed_by, Administrator):
            if self.performed_by.id != user.id:
                logger.error(f"User {self.performed_by.id} attempted to edit user {user.id} without permission.")
                raise PermissionViolationError()

    def _check_user_is_not_deleted(self, user: BaseUser) -> None:
        if user.is_deleted:
            logger.error(f"Attempted operation on deleted user ID {user.id}.")
            raise NotFoundError(self.USER_NOT_FOUND)

    def _check_can_edit_inactive(self, user: BaseUser) -> None:
        if not has_role(self.performed_by, Administrator):
            if not user.is_active:
                logger.error(
                    f"User {self.performed_by.id} attempted to edit inactive user {user.id} without permission."
                )
                raise PermissionViolationError()

    def _validate_passwords(self, password: str | None, another_password: str | None) -> None:
        if password is None or password.strip() == "":
            return

        try:
            validate_password(password)
        except ValidationError as e:
            logger.error(f"Password validation failed: {e.messages}")
            raise ApplicationError(self.PASSWORD_IS_INVALID)

        if password != another_password:
            logger.error("Password and confirmation password do not match.")
            raise ApplicationError(self.PASSWORDS_DONT_MATCH)

    def _anonymize_user_data(self, user: BaseUser) -> None:
        user.name = generate_randon_string(10)
        user.surname = generate_randon_string(10)
        user.username = generate_randon_string(10)
        user.email = generate_random_email()

    def _check_email_sending_delay(self, user) -> None:
        last_email_time = user.verification_email_sent_at

        if last_email_time:
            elapsed_time = timezone.now() - last_email_time

            if elapsed_time < (delay_end_time := datetime.timedelta(minutes=settings.EMAIL_SENDING_DELAY_MINUTES)):
                logger.error(f"User {self.performed_by.id} attempted to resend verification email too soon.")

                raise EmailDelayError(wait_time=delay_end_time - elapsed_time)

    def _check_is_already_verified(self, user: BaseUser) -> None:
        if user.is_verified:
            logger.error(f"User {user.id} attempted to verify an already verified email.")
            raise ApplicationError(self.USER_IS_ALREADY_VERIFIED)

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def create_user(
        self, name: str, surname: str, email: str, username: str, password: str, another_password: str, is_admin: bool
    ) -> BaseUser:
        self._check_permission_to_create_admin(is_admin)
        self._validate_passwords(password, another_password)

        logger.debug(f"Creating user with email: {email}, username: {username}, is_admin: {is_admin}")

        user = BaseUser(name=name, surname=surname, email=email, username=username, is_admin=is_admin)
        user.set_password(password)

        self._handle_verification(user)

        user = self.base_service.create_base(user, self.performed_by)

        self._assign_role(user, is_admin)

        logger.info(f"Created new user: {user.email} (ID: {user.id})")

        return user

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def edit_user(
        self,
        id: UUID,
        name: str,
        surname: str,
        email: str,
        username: str,
        is_admin: bool,
        password: str | None = None,
        another_password: str | None = None,
    ) -> BaseUser:
        self._check_permission_to_create_admin(is_admin)
        self._validate_passwords(password, another_password)

        user = get_object_or_raise(BaseUser, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_owner_or_admin(user)
        self._check_user_is_not_deleted(user)
        self._check_can_edit_inactive(user)

        logger.debug(f"Editing user ID {user.id} with email: {email}, username: {username}, is_admin: {is_admin}")

        user.name = name
        user.surname = surname
        user.username = username
        user.is_admin = is_admin

        if password:
            user.set_password(password)

        if user.email != email:
            user.email = email
            user.is_verified = False
            self._handle_verification(user)

        user = self.base_service.edit_base(user, self.performed_by)

        self._assign_role(user, is_admin)

        logger.info(f"Edited user: {user.email} (ID: {user.id})")

        return user

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def delete_user(self, id: UUID) -> None:
        user = get_object_or_raise(BaseUser, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_owner_or_admin(user)
        self._check_user_is_not_deleted(user)
        self._check_can_edit_inactive(user)

        logger.debug(f"Soft-deleting user: {user.id}")

        self._anonymize_user_data(user)

        user.is_deleted = True

        self.base_service.edit_base(user, self.performed_by)

        logger.info(f"Soft-deleted user: {user.id}")

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def send_verification_email(self, id: UUID) -> None:
        user = get_object_or_raise(BaseUser, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_owner_or_admin(user)
        self._check_user_is_not_deleted(user)
        self._check_can_edit_inactive(user)
        self._check_email_sending_delay(user)
        self._check_is_already_verified(user)

        logger.debug(f"Resending verification email to user ID {user.id}")

        self._handle_verification(user)

        self.base_service.edit_base(user, self.performed_by)

        logger.info(f"Resent verification email to user ID {user.id}")

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def verify_user_email(self, id: UUID, verification_code: str) -> None:
        user = get_object_or_raise(BaseUser, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_owner_or_admin(user)
        self._check_user_is_not_deleted(user)
        self._check_can_edit_inactive(user)
        self._check_is_already_verified(user)

        logger.debug(f"Verifying user: {user.id}")

        if (
            user.verification_code is None
            or user.verification_code != verification_code
            or user.verification_code_expires_at is None
            or timezone.now() > user.verification_code_expires_at
        ):
            logger.error(f"Invalid or expired verification code for user ID {user.id}")
            raise ApplicationError(self.VERIFICATION_FAILED)

        user.is_verified = True

        self.base_service.edit_base(user, self.performed_by)

        logger.info(f"Verified user: {user.id}")

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def moderate_user(self, id: UUID, action: ModerationAction) -> None:
        user = get_object_or_raise(BaseUser, self.NOT_FOUND_MESSAGE, id=id)

        self._check_user_is_not_deleted(user)

        if action == ModerationAction.BAN and not user.is_active:
            logger.error(f"Attempted to ban already inactive user ID {user.id}.")
            raise ApplicationError(self.USER_IS_ALREADY_BANNED)

        if action == ModerationAction.UNBAN and user.is_active:
            logger.error(f"Attempted to unban already active user ID {user.id}.")
            raise ApplicationError(self.USER_IS_NOT_BANNED)

        match action:
            case ModerationAction.BAN:
                user.is_active = False

            case ModerationAction.UNBAN:
                user.is_active = True

        self.base_service.edit_base(user, self.performed_by)

        logger.info(f"Moderation action '{action.value}' performed on user: {user.id}.")
