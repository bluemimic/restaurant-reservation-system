from typing import Type

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import BaseForm
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View
from rolepermissions.checkers import has_role

from src.common.mixins import HandleErrorsMixin, RoleBasedAccessMixin
from src.common.utils import bootstrapify_form, get_object_or_raise, paginate_queryset, prepare_get_params
from src.common.views import BaseFormView
from src.core.exceptions import ApplicationError
from src.core.roles import Administrator, Restaurant
from src.reservations.forms import (
    CartAddForm,
    CartCheckoutForm,
    ReservationCreateForm,
    ReservationEditForm,
)
from src.reservations.models import Reservation
from src.reservations.selectors import ReservationFilterSet, ReservationSelectors
from src.reservations.services import ReservationService
from src.reservations.cart import (
    add_to_cart,
    clear_cart,
    get_cart_items,
    remove_from_cart,
    update_cart_item,
    validate_cart_portions,
)
from src.offers.models import Offer


def _get_create_form(request) -> Type[BaseForm]:
    return ReservationCreateForm


def _get_edit_form(request) -> Type[BaseForm]:
    return ReservationEditForm


class ReservationCreateView(RoleBasedAccessMixin, BaseFormView):
    template_name = "reservations/reservation_create.html"
    required_roles = [Restaurant]
    allow_guests = True
    success_message = _("Reservation has been successfully created!")

    def get_form_class(self, request, *args, **kwargs) -> Type[BaseForm]:
        return _get_create_form(request)

    def get_form(self, request, *args, **kwargs):
        form_class = self.get_form_class(request, *args, **kwargs)
        initial = {}

        if offer_id := request.GET.get("offer"):
            initial["offer"] = offer_id

        if restaurant_id := request.GET.get("restaurant"):
            initial["restaurant"] = restaurant_id

        return form_class(request.POST or None, request.FILES or None, initial=initial)

    def form_valid(self, request, form, *args, **kwargs):
        performed_by = request.user if request.user.is_authenticated else None
        service = ReservationService(performed_by=performed_by)

        reservation = service.create_reservation(
            client_name=form.cleaned_data["client_name"],
            restaurant_id=form.cleaned_data["restaurant"].id,
            portions_reserved=form.cleaned_data["portions_reserved"],
            offer_id=form.cleaned_data["offer"].id if form.cleaned_data.get("offer") else None,
            table_number=form.cleaned_data["table_number"],
        )

        messages.success(
            request,
            _("Reservation confirmed for %(client)s — %(portions)s portion(s) reserved.")
            % {
                "client": reservation.client_name,
                "portions": reservation.portions_reserved,
            },
        )

        if request.user.is_authenticated:
            return redirect("reservations:detail", id=reservation.id)

        return redirect("offers:list")


class ReservationEditView(LoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "reservations/reservation_edit.html"
    required_roles = [Administrator, Restaurant]
    success_message = _("Reservation has been successfully updated!")

    def get_form_class(self, request, *args, **kwargs):
        return _get_edit_form(request)

    def get_instance(self, request, *args, **kwargs) -> object | None:
        selectors = ReservationSelectors()
        return selectors.get_reservation_by_id(kwargs["id"])

    def form_valid(self, request, form, *args, **kwargs):
        service = ReservationService(performed_by=request.user)

        reservation = service.edit_reservation(
            id=kwargs.get("id"),
            client_name=form.cleaned_data.get("client_name"),
            table_number=form.cleaned_data.get("table_number"),
            portions_reserved=form.cleaned_data.get("portions_reserved"),
        )

        messages.success(request, self.success_message)

        return redirect("reservations:detail", id=kwargs.get("id"))


class ReservationDetailView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "reservations/reservation_detail.html"
    required_roles = [Administrator, Restaurant]

    def get(self, request, *args, **kwargs):
        requested_id = kwargs.get("id")

        selectors = ReservationSelectors()
        reservation = selectors.get_reservation_by_id(requested_id)

        return render(request, self.template_name, {"reservation": reservation})


class ReservationListView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "reservations/reservation_list.html"
    required_roles = [Administrator, Restaurant]

    def get(self, request, *args, **kwargs):
        filters = request.GET.copy()

        if has_role(request.user, Restaurant) and not has_role(request.user, Administrator):
            filters["restaurant"] = str(request.user.id)

        selectors = ReservationSelectors()
        qs = selectors.get_reservations(filters=filters)

        page_obj = paginate_queryset(request, qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(
            ReservationFilterSet(data=filters, queryset=Reservation.objects.all()).form
        )

        context = {"page_obj": page_obj, "querystring": querystring}
        context.update({"filter_form": filter_form})
        return render(request, self.template_name, context)


class ReservationDeleteView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator, Restaurant]
    success_message = _("Reservation has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        requested_id = kwargs.get("id")

        service = ReservationService(performed_by=request.user)
        service.cancel_reservation(requested_id)

        messages.success(request, self.success_message)

        if has_role(request.user, Administrator):
                return redirect("reservations:list")

        return redirect("offers:list")


class ReservationStatusView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator, Restaurant]
    success_message = _("Reservation status updated.")

    def post(self, request, *args, **kwargs):
        new_status = request.POST.get("status")

        if new_status not in Reservation.ReservationStatus.values:
            messages.error(request, _("Invalid status."))
            return redirect("reservations:detail", id=kwargs["id"])

        service = ReservationService(performed_by=request.user)
        service.change_status(kwargs["id"], new_status)

        messages.success(request, self.success_message)

        return redirect("reservations:detail", id=kwargs["id"])


class CartView(HandleErrorsMixin, View):
    template_name = "reservations/cart.html"

    def get(self, request, *args, **kwargs):
        cart_items = get_cart_items(request)

        return render(request, self.template_name, {"cart_items": cart_items})


class CartAddView(HandleErrorsMixin, View):
    def post(self, request, id, *args, **kwargs):
        offer = get_object_or_raise(Offer, _("Offer not found."), id=id)
        form = CartAddForm(request.POST)

        if not form.is_valid():
            messages.error(request, _("Please enter a valid number of portions."))
            next_url = request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("offers:detail", id=id)

        portions = form.cleaned_data["portions"]

        try:
            validate_cart_portions(request, offer, portions)
            add_to_cart(request, offer.id, portions)
        except ApplicationError as e:
            messages.error(request, e.message)
            next_url = request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("offers:detail", id=id)

        messages.success(
            request,
            _("%(portions)s portion(s) of %(food)s added to your cart.")
            % {"portions": portions, "food": offer.name},
        )

        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)

        return redirect("reservations:cart")


class CartRemoveView(HandleErrorsMixin, View):
    def post(self, request, id, *args, **kwargs):
        remove_from_cart(request, id)
        messages.success(request, _("Item removed from your cart."))

        return redirect("reservations:cart")


class CartUpdateView(HandleErrorsMixin, View):
    def post(self, request, id, *args, **kwargs):
        offer = get_object_or_raise(Offer, _("Offer not found."), id=id)
        form = CartAddForm(request.POST)

        if not form.is_valid():
            messages.error(request, _("Please enter a valid number of portions."))
            return redirect("reservations:cart")

        portions = form.cleaned_data["portions"]

        if portions > offer.portions_available:
            messages.error(
                request,
                _("Not enough portions available for %(food)s. Only %(count)s left.")
                % {"food": offer.name, "count": offer.portions_available},
            )
            return redirect("reservations:cart")

        update_cart_item(request, offer.id, portions)
        messages.success(request, _("Cart updated."))

        return redirect("reservations:cart")


class CartCheckoutView(HandleErrorsMixin, View):
    template_name = "reservations/cart_checkout.html"
    confirmation_template_name = "reservations/cart_confirmation.html"

    def get(self, request, *args, **kwargs):
        cart_items = get_cart_items(request)

        if not cart_items:
            messages.info(request, _("Your cart is empty. Browse offers to add food."))
            return redirect("offers:list")

        form = bootstrapify_form(CartCheckoutForm())

        return render(request, self.template_name, {"cart_items": cart_items, "form": form})

    def post(self, request, *args, **kwargs):
        cart_items = get_cart_items(request)

        if not cart_items:
            messages.info(request, _("Your cart is empty. Browse offers to add food."))
            return redirect("offers:list")

        form = CartCheckoutForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"cart_items": cart_items, "form": bootstrapify_form(form)},
            )

        performed_by = request.user if request.user.is_authenticated else None
        service = ReservationService(performed_by=performed_by)

        try:
            reservations = service.checkout_cart(
                client_name=form.cleaned_data["client_name"],
                client_phone=form.cleaned_data["client_phone"],
                cart_lines=[(item["offer"].id, item["portions"]) for item in cart_items],
            )
        except ApplicationError as e:
            messages.error(request, e.message)
            return render(
                request,
                self.template_name,
                {"cart_items": get_cart_items(request), "form": bootstrapify_form(form)},
            )

        clear_cart(request)

        messages.success(
            request,
            _("Your reservations have been submitted. Each restaurant will confirm your order."),
        )

        return render(
            request,
            self.confirmation_template_name,
            {
                "reservations": reservations,
                "client_name": form.cleaned_data["client_name"],
                "client_phone": form.cleaned_data["client_phone"],
            },
        )
