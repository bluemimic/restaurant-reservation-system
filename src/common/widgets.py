from django.forms.widgets import CheckboxSelectMultiple


class BootstrapCheckboxSelectMultiple(CheckboxSelectMultiple):
    option_template_name = "core/widgets/bootstrap_checkbox_option.html"
