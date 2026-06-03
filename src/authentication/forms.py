from django import forms
from django.utils.translation import gettext_lazy as _

from src.common.forms import FIELD_INVALID, FIELD_REQUIRED


class LoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        label=_("Email"),
        max_length=255,
        error_messages={
            "invalid": FIELD_INVALID.format(field=_("Email")),
            "required": FIELD_REQUIRED.format(field=_("Email")),
        },
    )
    password = forms.CharField(
        required=True,
        label=_("Password"),
        widget=forms.PasswordInput,
        error_messages={
            "required": FIELD_REQUIRED.format(field=_("Password")),
        },
    )
