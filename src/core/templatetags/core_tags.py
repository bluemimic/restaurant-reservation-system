from django import template

register = template.Library()


@register.filter
def to_decimal(value: float) -> str:
    return f"{value:.2f}"


@register.filter
def status_label(status: str) -> str:
    return status.replace("_", " ")


@register.filter
def get_item(mapping, key):
    if mapping is None:
        return None
    return mapping.get(key)
