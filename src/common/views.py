from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.forms import BaseForm
from django.shortcuts import render
from django.views import View

from src.common.mixins import HandleErrorsMixin
from src.common.utils import bootstrapify_form
from src.core.exceptions import ApplicationError


class BaseFormView(HandleErrorsMixin, View):
    form_class: type[BaseForm] | None = None
    template_name: str | None = None

    def get_form_class(self, request, *args, **kwargs) -> type[BaseForm]:
        if self.form_class is None:
            raise ImproperlyConfigured("form_class must be provided or get_form_class overridden")
        return self.form_class

    def get_form(self, request, *args, **kwargs):
        form_class = self.get_form_class(request, *args, **kwargs)
        _instance = self.get_instance(request, *args, **kwargs)

        return form_class(request.POST or None, request.FILES or None, instance=_instance)

    def get_extra_context(self, request, form, *args, **kwargs) -> dict:
        return {}

    def get_instance(self, request, *args, **kwargs) -> object | None:
        return None

    def build_context(self, request, form, *args, **kwargs) -> dict:
        context = self.get_extra_context(request, form, *args, **kwargs)
        context["form"] = bootstrapify_form(form)

        return context

    def render_form(self, request, form, *args, **kwargs):
        context = self.build_context(request, form, *args, **kwargs)

        return render(request, self.template_name, context)

    def ensure_access(self, request, *args, **kwargs) -> None:
        pass

    def get(self, request, *args, **kwargs):
        self.ensure_access(request, *args, **kwargs)

        form = self.get_form(request, *args, **kwargs)

        return self.render_form(request, form)

    def post(self, request, *args, **kwargs):
        self.ensure_access(request, *args, **kwargs)

        form = self.get_form(request, *args, **kwargs)

        if form.is_valid():
            try:
                return self.form_valid(request, form, *args, **kwargs)

            except ApplicationError as e:
                form.add_error(None, e.message)

                return self.render_form(request, form, *args, **kwargs)

            except ValidationError as e:
                form.add_error(None, str(e))

                return self.render_form(request, form, *args, **kwargs)

        return self.form_invalid(request, form, *args, **kwargs)

    def form_valid(self, request, form, *args, **kwargs):
        raise ImproperlyConfigured("You must override form_valid() in your BaseFormView subclasses.")

    def form_invalid(self, request, form, *args, **kwargs):
        return self.render_form(request, form, *args, **kwargs)
