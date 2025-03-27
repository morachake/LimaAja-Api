from django import template

register = template.Library()

@register.filter
def percentage_of(value, total):
    """
    Calculate what percentage of total a value is
    """
    try:
        return int(float(value) / float(total) * 100)
    except (ValueError, ZeroDivisionError):
        return 0

