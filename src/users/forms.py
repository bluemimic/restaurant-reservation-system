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


class UserEditForm(UserCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].required = False
        self.fields["another_password"].required = False


class UserEditAdminForm(UserCreateAdminForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].required = False
        self.fields["another_password"].required = False
