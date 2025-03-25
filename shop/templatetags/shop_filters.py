from django import template

register = template.Library()

@register.filter
def filter_by_category(products, category):
    """Filter products by category"""
    if not products or not category:
        return []
    return [p for p in products if hasattr(p, 'produce_type') and hasattr(p.produce_type, 'category') and p.produce_type.category == category]

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''