from typing import Optional, Type

from django.core.exceptions import ValidationError
from django.core.paginator import Page, Paginator
from django.db.models import QuerySet
from django.forms import Form
from django.forms.widgets import CheckboxInput, Select, SelectMultiple
from django.utils.translation import gettext as _
from loguru import logger

from src.common.forms import FIELD_INVALID, FIELD_REQUIRED
from src.common.types import DjangoModelType
from src.core.exceptions import NotFoundError


def get_object_or_none(model: Type[DjangoModelType], **kwargs) -> Optional[DjangoModelType]:
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def get_object_or_raise(model: Type[DjangoModelType], message: str, **kwargs) -> DjangoModelType:
    obj = get_object_or_none(model, **kwargs)

    if obj is None:
        logger.error(f"Object not found: {model.__name__} with {kwargs}")
        raise NotFoundError(message)

    return obj


def bootstrapify_form(form: Form, floating: bool = False) -> Form:
    for field in form.__iter__():
        if isinstance(field.field.widget, CheckboxInput):
            field.field.widget.attrs["class"] = "form-check-input"
        elif isinstance(field.field.widget, (Select, SelectMultiple)):
            field.field.widget.attrs["class"] = "form-select"
        else:
            field.field.widget.attrs["class"] = "form-control"

        if floating:
            field.field.widget.attrs["placeholder"] = " "

        if field.errors:
            field.field.widget.attrs["class"] += " is-invalid"

    return form


def generate_model_form_errors(fields: list[str], model: type[DjangoModelType]) -> dict[str, dict[str, str]]:
    errors: dict[str, dict[str, str]] = {}

    for field in fields:
        label = None

        try:
            field_obj = model._meta.get_field(field)
            label = str(field_obj.verbose_name)
        except Exception:
            label = None

        if not label:
            label = field.replace("_", " ").capitalize()

        translated_label = _(label)

        errors[field] = {
            "required": FIELD_REQUIRED.format(field=translated_label),
            "invalid": FIELD_INVALID.format(field=translated_label),
            "invalid_pk_value": FIELD_INVALID.format(field=translated_label),
            "invalid_choice": FIELD_INVALID.format(field=translated_label),
            "invalid_list": FIELD_INVALID.format(field=translated_label),
            "max_length": FIELD_INVALID.format(field=translated_label),
        }

    return errors


def is_htmx_request(request) -> bool:
    return request.headers.get("HX-Request") == "true" or request.META.get("HTTP_HX_REQUEST") == "true"


def paginate_queryset(request, queryset: QuerySet, per_page: int = 10) -> Page:
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page", 1)

    page_obj = paginator.get_page(page_number)

    return page_obj


def _is_unique_error(e: ValidationError) -> bool:
    if not hasattr(e, "error_dict"):
        return False

    for field_errors in e.error_dict.values():
        for error in field_errors:
            if error.code in ("unique", "unique_together"):
                return True
    return False


def prepare_get_params(request, exclude: list[str] | None = None) -> str:
    exclude = exclude or []
    params = request.GET.copy()

    for param in exclude:
        if param in params:
            params.pop(param)

    querystring = params.urlencode()

    return querystring
