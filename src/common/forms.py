from django.utils.translation import gettext_lazy as _

FIELD_INVALID = _("Field {field} is not valid!")
FIELD_REQUIRED = _("Field {field} is required!")


class ErrorMessageFormMixin:
    def apply_error_messages(self):
        meta = getattr(self, "Meta", None)
        
        if not meta:
            return

        error_map = getattr(meta, "error_messages", {})
        
        if not error_map:
            return

        for field_name, messages in error_map.items():
            if field_name in self.fields:
                self.fields[field_name].error_messages.update(messages)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_error_messages()
