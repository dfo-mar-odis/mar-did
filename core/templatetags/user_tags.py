# core/templatetags/user_tags.py
from django import template

register = template.Library()

@register.filter(name='is_maintainer')
def is_maintainer(user):
    """Check if user belongs to MarDID Maintainer group"""
    if user.is_authenticated:
        return user.is_superuser or user.groups.filter(name='MarDID Maintainers').exists()
    return False


@register.filter(name='is_chief_scientist')
def is_chief_scientist(user):
    """Check if user belongs to MarDID Maintainer group"""
    if user.is_authenticated:
        return user.is_superuser or user.groups.filter(name='Chief Scientists').exists()

    return False