from uuid import UUID

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from loguru import logger

from src.common.services import BaseService
from src.common.utils import get_object_or_raise
from src.core.exceptions import ApplicationError
from src.offers.models import Offer
from src.users.models import Restaurant

from .models import Reservation


class ReservationService:
    """
    Used by restaurants to manage reservations (change status).
    For anonymous visitor actions (create, edit, cancel) use ReservationVisitorService.
    """

    def __init__(
        self,
        performed_by: Restaurant,
        base_service: BaseService[Reservation] | None = None,
    ) -> None:
        self.performed_by = performed_by
        self.base_service: BaseService[Reservation] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Reservation not found.")
    WRONG_RESTAURANT_MESSAGE = _("This reservation does not belong to your restaurant.")
    INVALID_STATUS_TRANSITION_MESSAGE = _("This status change is not allowed.")

    # Defines which statuses a restaurant is allowed to transition to
    ALLOWED_TRANSITIONS: dict[str, list[str]] = {
        Reservation.ReservationStatus.CREATED: [
            Reservation.ReservationStatus.ACCEPTED,
            Reservation.ReservationStatus.DENIED,
        ],
        Reservation.ReservationStatus.ACCEPTED: [
            Reservation.ReservationStatus.PREPARED,
        ],
        Reservation.ReservationStatus.PREPARED: [
            Reservation.ReservationStatus.DELIVERED,
        ],
    }

    def _check_is_own_reservation(self, reservation: Reservation) -> None:
        if reservation.restaurant_id != self.performed_by.id:
            logger.error(
                f"Restaurant {self.performed_by.id} attempted to modify "
                f"reservation {reservation.id} belonging to another restaurant."
            )
            raise ApplicationError(self.WRONG_RESTAURANT_MESSAGE)

    def _check_status_transition(self, reservation: Reservation, new_status: str) -> None:
        allowed = self.ALLOWED_TRANSITIONS.get(reservation.reservation_status, [])
        if new_status not in allowed:
            logger.error(
                f"Invalid status transition for reservation {reservation.id}: "
                f"{reservation.reservation_status} -> {new_status}"
            )
            raise ApplicationError(self.INVALID_STATUS_TRANSITION_MESSAGE)

    @transaction.atomic
    def change_status(self, id: UUID, new_status: str) -> Reservation:
        reservation = get_object_or_raise(Reservation, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_own_reservation(reservation)
        self._check_status_transition(reservation, new_status)

        logger.debug(f"Changing reservation {reservation.id} status: {reservation.reservation_status} -> {new_status}")

        reservation.reservation_status = new_status

        reservation = self.base_service.edit_base(reservation, self.performed_by)

        logger.info(f"Reservation {reservation.id} status changed to {new_status}")

        return reservation


class ReservationService:
    """
    Used by anonymous visitors: create, edit, cancel a reservation.
    No performed_by since visitors are not authenticated.
    """

    def __init__(self, base_service: BaseService[Reservation] | None = None) -> None:
        self.base_service: BaseService[Reservation] = base_service or BaseService()

    NOT_FOUND_MESSAGE = _("Reservation not found.")
    OFFER_NOT_FOUND_MESSAGE = _("Offer not found.")
    NOT_EDITABLE_MESSAGE = _("Only reservations in 'created' status can be modified.")
    NOT_ENOUGH_PORTIONS_MESSAGE = _("Not enough portions available for this offer.")

    def _check_is_editable(self, reservation: Reservation) -> None:
        if reservation.reservation_status != Reservation.ReservationStatus.CREATED:
            raise ApplicationError(self.NOT_EDITABLE_MESSAGE)

    def _check_portions_available(self, offer: Offer, requested: int) -> None:
        if offer.portions_available < requested:
            raise ApplicationError(self.NOT_ENOUGH_PORTIONS_MESSAGE)

    @transaction.atomic
    def create_reservation(
        self,
        client_name: str,
        table_number: int,
        restaurant_id: UUID,
        portions_reserved: int,
        offer_id: UUID | None = None,
    ) -> Reservation:
        offer = None

        if offer_id is not None:
            offer = get_object_or_raise(Offer, self.OFFER_NOT_FOUND_MESSAGE, id=offer_id)
            self._check_portions_available(offer, portions_reserved)

            offer.portions_available -= portions_reserved
            offer.save()

        logger.debug(f"Creating reservation for client: {client_name}, table: {table_number}")

        reservation = Reservation(
            client_name=client_name,
            table_number=table_number,
            restaurant_id=restaurant_id,
            portions_reserved=portions_reserved,
            offer=offer,
        )

        reservation = self.base_service.create_base(reservation)

        logger.info(f"Created reservation ID: {reservation.id}")

        return reservation

    @transaction.atomic
    def edit_reservation(
        self,
        id: UUID,
        client_name: str,
        table_number: int,
        portions_reserved: int,
    ) -> Reservation:
        reservation = get_object_or_raise(Reservation, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_editable(reservation)

        if reservation.offer and portions_reserved != reservation.portions_reserved:
            # Give back old portions, check and deduct new amount
            reservation.offer.portions_available += reservation.portions_reserved
            self._check_portions_available(reservation.offer, portions_reserved)
            reservation.offer.portions_available -= portions_reserved
            reservation.offer.save()

        logger.debug(f"Editing reservation {reservation.id}")

        reservation.client_name = client_name
        reservation.table_number = table_number
        reservation.portions_reserved = portions_reserved

        reservation = self.base_service.edit_base(reservation)

        logger.info(f"Edited reservation ID: {reservation.id}")

        return reservation

    @transaction.atomic
    def cancel_reservation(self, id: UUID) -> None:
        reservation = get_object_or_raise(Reservation, self.NOT_FOUND_MESSAGE, id=id)

        self._check_is_editable(reservation)

        logger.debug(f"Cancelling reservation {reservation.id}")

        if reservation.offer:
            reservation.offer.portions_available += reservation.portions_reserved
            reservation.offer.save()

        reservation.reservation_status = Reservation.ReservationStatus.CANCELED

        self.base_service.edit_base(reservation)

        logger.info(f"Cancelled reservation ID: {reservation.id}")
