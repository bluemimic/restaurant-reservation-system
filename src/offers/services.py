from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from loguru import logger

from src.common.services import BaseService
from src.common.utils import get_object_or_raise
from src.core.exceptions import ApplicationError
from src.users.models import Restaurant

from .models import Offer


class OfferService:
    def __init__(
        self,
        performed_by: Restaurant,
        base_service: BaseService[Offer] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[Offer] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Offer not found.")
    NOT_OWNER_MESSAGE = _("You can only modify your own offers.")
    INVALID_PORTIONS_MESSAGE = _("Portions available cannot be negative.")

    def _check_is_owner(self, offer: Offer) -> None:
        if offer.restaurant_id != self.performed_by.id:
            logger.error(f"Restaurant {self.performed_by.id} attempted to modify offer {offer.id} they don't own.")
            raise ApplicationError(self.NOT_OWNER_MESSAGE)

    @transaction.atomic
    def create_offer(
        self,
        name: str,
        price: Decimal,
        portions_available: int,
        category: str,
        description: str | None = None,
        image=None,
    ) -> Offer:
        logger.debug(f"Restaurant {self.performed_by.id} creating offer: {name}")

        offer = Offer(
            name=name,
            price=price,
            portions_available=portions_available,
            category=category,
            description=description,
            image=image,
            restaurant=self.performed_by,
        )

        offer = self.base_service.create_base(offer, self.performed_by)

        logger.info(f"Created offer: {offer.name} (ID: {offer.id})")

        return offer

    @transaction.atomic
    def edit_offer(
        self,
        id: UUID,
        name: str,
        price: Decimal,
        portions_available: int,
        category: str,
        description: str | None = None,
        image=None,
    ) -> Offer:
        offer = get_object_or_raise(Offer, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_owner(offer)

        logger.debug(f"Editing offer {offer.id}")

        offer.name = name
        offer.price = price
        offer.portions_available = portions_available
        offer.category = category
        offer.description = description
        offer.image = image

        offer = self.base_service.edit_base(offer, self.performed_by)

        logger.info(f"Edited offer: {offer.name} (ID: {offer.id})")

        return offer

    @transaction.atomic
    def delete_offer(self, id: UUID) -> None:
        offer = get_object_or_raise(Offer, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_owner(offer)

        logger.debug(f"Deleting offer {offer.id}")

        self.base_service.delete_base(offer)

        logger.info(f"Deleted offer ID: {id}")

    @transaction.atomic
    def update_portions(self, id: UUID, portions_available: int) -> Offer:
        offer = get_object_or_raise(Offer, self.NOT_FOUND_MESSAGE, id=id)

        if portions_available < 0:
            raise ApplicationError(self.INVALID_PORTIONS_MESSAGE)

        logger.debug(f"Updating portions for offer {offer.id} to {portions_available}")

        offer.portions_available = portions_available

        offer = self.base_service.edit_base(offer, self.performed_by)

        logger.info(f"Updated portions for offer {offer.id}: {portions_available} remaining")

        return offer
