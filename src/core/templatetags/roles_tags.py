from django import template
from rolepermissions.checkers import has_role

from src.core.roles import Administrator

register = template.Library()

@register.simple_tag
def is_admin(user):
    return user.is_authenticated and has_role(user, Administrator)
