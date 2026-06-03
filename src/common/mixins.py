from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext as _
from rolepermissions.checkers import has_role
from rolepermissions.roles import AbstractUserRole

from src.common.utils import is_htmx_request
from src.core.exceptions import ApplicationError, DomainError, NotFoundError, PermissionViolationError


class RoleBasedAccessMixin(AccessMixin):
    required_roles: list[type[AbstractUserRole]] = []
    allow_guests: bool = False
    raise_exception: bool = True

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated or not user.is_active:
            if self.allow_guests:
                return super().dispatch(request, *args, **kwargs)

            messages.error(request, _("Access denied!"))
            return self.handle_no_permission()

        if not any(has_role(user, role) for role in self.required_roles):
            messages.error(request, _("Access denied!"))
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class HandleErrorsMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)

        except PermissionViolationError as e:
            messages.error(request, e.message)

            if is_htmx_request(request):
                return render(request, "core/_messages_oob.html", {})

            return self.handle_no_permission()

        except NotFoundError as e:
            messages.error(request, e.message)
            raise Http404(e.message)

        except ApplicationError as e:
            messages.error(request, e.message)

            if is_htmx_request(request):
                return render(request, "core/_messages_oob.html", {})

            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        except DomainError as e:
            messages.error(request, e.message)

            if is_htmx_request(request):
                return render(request, "core/_messages_oob.html", {})

            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
