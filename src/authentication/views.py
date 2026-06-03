from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View

from src.authentication.forms import LoginForm
from src.authentication.services import AuthService
from src.common.utils import bootstrapify_form
from src.core.exceptions import ApplicationError


class LoginView(View):
    template_name = "auth/login.html"
    success_message = _("User has successfully logged in!")

    def _redirect(self, request):
        next_url = request.GET.get("next")

        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)

        return redirect(settings.LOGIN_REDIRECT_URL)

    def get(self, request, *args, **kwargs):
        form = LoginForm()
        form = bootstrapify_form(form)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            auth_service = AuthService(request)

            try:
                auth_service.login(email=email, password=password)

                messages.success(request, self.success_message)
                return self._redirect(request)

            except ApplicationError as e:
                form.add_error(None, e.message)

        form = bootstrapify_form(form)
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    success_message = _("User has successfully logged out!")

    def get(self, request, *args, **kwargs):
        auth_service = AuthService(request)
        auth_service.logout()

        messages.success(request, self.success_message)

        return redirect("home:index")
