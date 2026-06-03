from typing import Type

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import BaseForm
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from src.common.mixins import HandleErrorsMixin, RoleBasedAccessMixin
from src.common.utils import bootstrapify_form, paginate_queryset, prepare_get_params
from src.common.views import BaseFormView
from src.core.roles import Administrator, Restaurant
from src.reservations.forms import ReservationCreateForm, ReservationEditForm
from src.reservations.selectors import ReservationFilterSet, ReservationSelectors
from src.reservations.services import ReservationService


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

    def form_valid(self, request, form, *args, **kwargs):
        service = ReservationService(performed_by=request.user if request.user.is_authenticated else None)

        reservation = service.create_reservation(
            client_name=form.cleaned_data["client_name"],
            table_number=form.cleaned_data["table_number"],
            restaurant_id=form.cleaned_data["restaurant"].id if form.cleaned_data.get("restaurant") else None,
            portions_reserved=form.cleaned_data["portions_reserved"],
            offer_id=form.cleaned_data.get("offer").id if form.cleaned_data.get("offer") else None,
        )

        messages.success(request, self.success_message)

        return redirect("reservations:detail", id=reservation.id)


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
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        selectors = ReservationSelectors()
        qs = selectors.get_reservations(filters=request.GET)

        page_obj = paginate_queryset(request, qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(ReservationFilterSet(request.GET).form)

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

        if hasattr(request.user, "id") and request.user.id:
            # If admin, go back to list; otherwise go to home
            from rolepermissions.checkers import has_role

            if has_role(request.user, Administrator):
                return redirect("reservations:list")

        return redirect("home:index")


# Create your views here.
