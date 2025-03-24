from django import template

register = template.Library()

@register.filter
def filter_by_category(products, category):
    """Filter products by category"""
    return [p for p in products if p.produce_type.category == category]

