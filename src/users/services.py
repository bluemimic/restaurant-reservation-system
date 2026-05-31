from uuid import UUID

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from loguru import logger

from src.common.services import BaseService
from src.common.utils import get_object_or_raise
from src.common.wrappers import handle_unique_error
from src.core.exceptions import ApplicationError

from .models import Restaurant


class RestaurantService:
    def __init__(
        self,
        performed_by: Restaurant,
        base_service: BaseService[Restaurant] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[Restaurant] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Restaurant not found.")
    UNIQUE_CONSTRAINT_MESSAGE = _("A restaurant with this email already exists.")
    PASSWORDS_DONT_MATCH = _("Passwords do not match.")
    PASSWORD_IS_INVALID = _(
        "Your password must contain at least one digit, one uppercase letter, and one special character."
    )

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

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def create_restaurant(self, name: str, email: str, password: str, another_password: str) -> Restaurant:
        self._validate_passwords(password, another_password)

        logger.debug(f"Creating restaurant with name: {name}, email: {email}")

        restaurant = Restaurant(name=name, email=email)
        restaurant.set_password(password)

        restaurant = self.base_service.create_base(restaurant, self.performed_by)

        logger.info(f"Created new restaurant: {restaurant.email} (ID: {restaurant.id})")

        return restaurant

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def edit_restaurant(
        self,
        id: UUID,
        name: str,
        email: str,
        password: str | None = None,
        another_password: str | None = None,
    ) -> Restaurant:
        self._validate_passwords(password, another_password)

        restaurant = get_object_or_raise(Restaurant, self.NOT_FOUND_MESSAGE, id=id)

        logger.debug(f"Editing restaurant ID {restaurant.id} with name: {name}, email: {email}")

        restaurant.name = name
        restaurant.email = email

        if password:
            restaurant.set_password(password)

        restaurant = self.base_service.edit_base(restaurant, self.performed_by)

        logger.info(f"Edited restaurant: {restaurant.email} (ID: {restaurant.id})")

        return restaurant

    @handle_unique_error(str(UNIQUE_CONSTRAINT_MESSAGE))
    @transaction.atomic
    def delete_restaurant(self, id: UUID) -> None:
        restaurant = get_object_or_raise(Restaurant, self.NOT_FOUND_MESSAGE, id=id)

        logger.debug(f"deleting restaurant: {restaurant.id}")
        # add deletion logic later

        #self.base_service.edit_base(restaurant, self.performed_by)

        logger.info(f"Soft-deleted restaurant: {restaurant.id}")
 
