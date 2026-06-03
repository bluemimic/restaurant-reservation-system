from django import template

register = template.Library()


@register.filter
def to_decimal(value: float) -> str:
    return f"{value:.2f}"
