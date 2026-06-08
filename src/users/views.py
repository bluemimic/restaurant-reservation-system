from typing import Type

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import BaseForm
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View
from rolepermissions.checkers import has_role

from src.authentication.services import AuthService
from src.common.mixins import (
    HandleErrorsMixin,
    RoleBasedAccessMixin,
)
from src.common.utils import bootstrapify_form, paginate_queryset, prepare_get_params
from src.common.views import BaseFormView
from src.core.exceptions import PermissionViolationError
from src.core.roles import Administrator, Restaurant
from src.users.forms import (
    UserCreateForm,
    UserEditAdminForm,
    UserEditForm,
)
from src.users.selectors import RestaurantFilterSet, RestaurantSelectors
from src.users.services import RestaurantService


def _get_create_form(request) -> Type[BaseForm]:
    return UserCreateForm


def _get_edit_form(request) -> Type[BaseForm]:
    if has_role(request.user, Administrator):
        return UserEditAdminForm
    return UserEditForm


class UserCreateView(LoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "users/user_create.html"
    required_roles = [Administrator]
    allow_guests = False
    success_message = _("Restaurant has been successfully created!")

    def get_form_class(self, request, *args, **kwargs) -> Type[BaseForm]:
        return _get_create_form(request)

    def form_valid(self, request, form, *args, **kwargs):
        user_service = RestaurantService(performed_by=request.user)

        user_service.create_restaurant(
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
            another_password=form.cleaned_data["another_password"],
            is_superuser=False,
        )

        messages.success(request, self.success_message)

        return redirect("users:list")


class UserEditView(LoginRequiredMixin, RoleBasedAccessMixin, BaseFormView):
    template_name = "users/user_edit.html"
    required_roles = [Administrator, Restaurant]
    success_message = _("Account has been successfully updated!")

    def get_form_class(self, request, *args, **kwargs):
        return _get_edit_form(request)

    def get_instance(self, request, *args, **kwargs) -> object | None:
        user_selectors = RestaurantSelectors(performed_by=request.user)

        return user_selectors.get_restaurant_by_id(kwargs["id"])

    def get_extra_context(self, request, form, *args, **kwargs) -> dict:
        return {"is_admin": has_role(request.user, Administrator)}

    def form_valid(self, request, form, *args, **kwargs):
        user_service = RestaurantService(performed_by=request.user)

        edit_kwargs = {
            "id": kwargs.get("id"),
            "name": form.cleaned_data.get("name"),
            "password": form.cleaned_data.get("password"),
            "another_password": form.cleaned_data.get("another_password"),
        }

        if has_role(request.user, Administrator):
            edit_kwargs["email"] = form.cleaned_data.get("email")
            edit_kwargs["is_superuser"] = form.cleaned_data.get("is_superuser", False)

        user = user_service.edit_restaurant(**edit_kwargs)

        update_session_auth_hash(request, user)

        messages.success(request, self.success_message)

        return redirect("users:detail", id=kwargs.get("id"))


class UserDetailView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "users/user_detail.html"
    required_roles = [Administrator, Restaurant]

    def get(self, request, *args, **kwargs):
        requested_user_id = kwargs.get("id")

        user_selectors = RestaurantSelectors(performed_by=request.user)
        user = user_selectors.get_restaurant_by_id(requested_user_id)

        if not has_role(request.user, Administrator) and user.id != request.user.id:
            raise PermissionViolationError()

        return render(
            request,
            self.template_name,
            {
                "user": user,
                "is_admin": has_role(request.user, Administrator),
            },
        )


class UserListView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    template_name = "users/user_list.html"
    required_roles = [Administrator]

    def get(self, request, *args, **kwargs):
        user_selectors = RestaurantSelectors(performed_by=request.user)
        users_qs = user_selectors.get_restaurants(filters=request.GET)

        page_obj = paginate_queryset(request, users_qs, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])
        filter_form = bootstrapify_form(RestaurantFilterSet(request.GET).form)

        context = {"page_obj": page_obj, "querystring": querystring}

        context.update({"filter_form": filter_form})
        return render(request, self.template_name, context)


class UserDeleteView(LoginRequiredMixin, RoleBasedAccessMixin, HandleErrorsMixin, View):
    required_roles = [Administrator]
    success_message = _("Restaurant has been successfully deleted!")

    def post(self, request, *args, **kwargs):
        requested_user_id = kwargs.get("id")

        user_service = RestaurantService(performed_by=request.user)
        user_service.delete_restaurant(requested_user_id)

        messages.success(request, self.success_message)

        return redirect("users:list")
