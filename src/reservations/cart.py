from uuid import UUID

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from src.core.exceptions import ApplicationError
from src.offers.models import Offer

CART_SESSION_KEY = "reservation_cart"


def _get_raw_cart(request: HttpRequest) -> list[dict]:
    return request.session.get(CART_SESSION_KEY, [])


def _save_cart(request: HttpRequest, cart: list[dict]) -> None:
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def get_cart_count(request: HttpRequest) -> int:
    return sum(item["portions"] for item in _get_raw_cart(request))


def clear_cart(request: HttpRequest) -> None:
    if CART_SESSION_KEY in request.session:
        del request.session[CART_SESSION_KEY]
        request.session.modified = True


def get_portions_in_cart(request: HttpRequest, offer_id: UUID) -> int:
    offer_id_str = str(offer_id)
    for item in _get_raw_cart(request):
        if item["offer_id"] == offer_id_str:
            return item["portions"]
    return 0


def add_to_cart(request: HttpRequest, offer_id: UUID, portions: int) -> None:
    cart = _get_raw_cart(request)
    offer_id_str = str(offer_id)

    for item in cart:
        if item["offer_id"] == offer_id_str:
            item["portions"] += portions
            _save_cart(request, cart)
            return

    cart.append({"offer_id": offer_id_str, "portions": portions})
    _save_cart(request, cart)


def remove_from_cart(request: HttpRequest, offer_id: UUID) -> None:
    offer_id_str = str(offer_id)
    cart = [item for item in _get_raw_cart(request) if item["offer_id"] != offer_id_str]
    _save_cart(request, cart)


def update_cart_item(request: HttpRequest, offer_id: UUID, portions: int) -> None:
    if portions <= 0:
        remove_from_cart(request, offer_id)
        return

    offer_id_str = str(offer_id)
    cart = _get_raw_cart(request)

    for item in cart:
        if item["offer_id"] == offer_id_str:
            item["portions"] = portions
            break

    _save_cart(request, cart)


def get_cart_items(request: HttpRequest) -> list[dict]:
    cart = _get_raw_cart(request)

    if not cart:
        return []

    offer_ids = [item["offer_id"] for item in cart]
    offers = Offer.objects.select_related("restaurant").in_bulk(offer_ids)

    items = []
    cleaned_cart = []

    for item in cart:
        offer = offers.get(UUID(item["offer_id"]))

        if offer is None or offer.portions_available <= 0:
            continue

        portions = min(item["portions"], offer.portions_available)
        items.append({"offer": offer, "portions": portions})
        cleaned_cart.append({"offer_id": item["offer_id"], "portions": portions})

    if cleaned_cart != cart:
        _save_cart(request, cleaned_cart)

    return items


def validate_cart_portions(request: HttpRequest, offer: Offer, portions: int) -> None:
    total = get_portions_in_cart(request, offer.id) + portions

    if portions <= 0:
        raise ApplicationError(_("Portions must be at least 1."))

    if total > offer.portions_available:
        raise ApplicationError(
            _("Not enough portions available for %(food)s. Only %(count)s left.")
            % {"food": offer.name, "count": offer.portions_available}
        )
