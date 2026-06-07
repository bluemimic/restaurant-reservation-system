from django import forms
from django.utils.translation import gettext_lazy as _

from src.common.utils import generate_model_form_errors
from src.users.models import Restaurant


class UserCreateForm(forms.ModelForm):
    another_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label=_("Confirm password"),
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        model = Restaurant
        fields = ["name", "email", "password", "another_password"]

        widgets = {
            "password": forms.PasswordInput(),
        }

        error_messages = generate_model_form_errors(fields, Restaurant)


class UserCreateAdminForm(UserCreateForm):
    class Meta(UserCreateForm.Meta):
        fields = UserCreateForm.Meta.fields + ["is_superuser"]

        error_messages = generate_model_form_errors(fields, Restaurant)


class UserEditForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label=_("New password"),
        help_text=_("Leave blank to keep your current password."),
    )
    another_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label=_("Confirm new password"),
        help_text=_("Enter the same password again for verification."),
    )

    class Meta:
        model = Restaurant
        fields = ["name"]
        labels = {
            "name": _("Name"),
        }


class UserEditAdminForm(UserCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].required = False
        self.fields["another_password"].required = False

    class Meta(UserCreateForm.Meta):
        fields = UserCreateForm.Meta.fields + ["is_superuser"]
        error_messages = generate_model_form_errors(UserCreateForm.Meta.fields + ["is_superuser"], Restaurant)
