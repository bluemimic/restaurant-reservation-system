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
from src.common.utils import bootstrapify_form, paginate_queryset, prepare_get_params
from src.common.views import BaseFormView
from src.core.roles import Administrator, Restaurant
from src.offers.forms import OfferCreateForm, OfferEditForm
from src.offers.selectors import OfferFilterSet, OfferSelectors
from src.offers.services import OfferService


def _get_create_form(request) -> Type[BaseForm]:
    return OfferCreateForm


def _get_edit_form(request) -> Type[BaseForm]:
    return OfferEditForm


class OfferListView(HandleErrorsMixin, View):
    template_name = "offers/offer_list.html"

    def get(self, request, *args, **kwargs):
        selectors = OfferSelectors()
        qs = selectors.get_offers(filters=request.GET)

        page_obj = paginate_queryset(request, qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(OfferFilterSet(request.GET).form)

        context = {"page_obj": page_obj, "querystring": querystring, "filter_form": filter_form}

        return render(request, self.template_name, context)


class OfferDetailView(HandleErrorsMixin, View):
    template_name = "offers/offer_detail.html"

    def get(self, request, *args, **kwargs):
        selectors = OfferSelectors()
        offer = selectors.get_offer_by_id(kwargs.get("id"))

        return render(request, self.template_name, {"offer": offer})


class OfferCreateView(LoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "offers/offer_create.html"
    required_roles = [Restaurant]
    allow_guests = False
    success_message = _("Offer has been successfully created!")

    def get_form_class(self, request, *args, **kwargs) -> Type[BaseForm]:
        return _get_create_form(request)

    def form_valid(self, request, form, *args, **kwargs):
        service = OfferService(performed_by=request.user)

        offer = service.create_offer(
            name=form.cleaned_data.get("name"),
            price=form.cleaned_data.get("price"),
            portions_available=form.cleaned_data.get("portions_available"),
            category=form.cleaned_data.get("category"),
            description=form.cleaned_data.get("description"),
            image=form.cleaned_data.get("image"),
        )

        messages.success(request, self.success_message)

        return redirect("offers:detail", id=offer.id)


class OfferEditView(LoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "offers/offer_edit.html"
    required_roles = [Administrator, Restaurant]
    success_message = _("Offer has been successfully updated!")

    def get_form_class(self, request, *args, **kwargs) -> Type[BaseForm]:
        return _get_edit_form(request)

    def get_instance(self, request, *args, **kwargs) -> object | None:
        selectors = OfferSelectors()
        return selectors.get_offer_by_id(kwargs.get("id"))

    def form_valid(self, request, form, *args, **kwargs):
        service = OfferService(performed_by=request.user)

        offer = service.edit_offer(
            id=kwargs.get("id"),
            name=form.cleaned_data.get("name"),
            price=form.cleaned_data.get("price"),
            portions_available=form.cleaned_data.get("portions_available"),
            category=form.cleaned_data.get("category"),
            description=form.cleaned_data.get("description"),
            image=form.cleaned_data.get("image"),
        )

        messages.success(request, self.success_message)

        return redirect("offers:detail", id=kwargs.get("id"))


class OfferDeleteView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator, Restaurant]
    success_message = _("Offer has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        requested_id = kwargs.get("id")

        service = OfferService(performed_by=request.user)
        service.delete_offer(requested_id)

        messages.success(request, self.success_message)

        if has_role(request.user, Administrator):
            return redirect("offers:list")

        return redirect("home:index")
