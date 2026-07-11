"""
tracker/templatetags/finance_tags.py

Custom template filters for the Finance Tracker.
Usage: {% load finance_tags %} at top of template.
"""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def abs_value(value):
    """Return the absolute value of a number."""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


@register.filter
def currency(value):
    """Format a number as Indian Rupee currency string."""
    try:
        v = Decimal(str(value))
        return f'₹{v:,.2f}'
    except Exception:
        return value


@register.filter
def percentage(value, decimals=1):
    """Format a number as a percentage string."""
    try:
        return f'{float(value):.{decimals}f}%'
    except (TypeError, ValueError):
        return '0%'


@register.filter
def progress_capped(value):
    """Cap a percentage at 100 for progress bar width (CSS max)."""
    try:
        return min(float(value), 100)
    except (TypeError, ValueError):
        return 0


@register.filter
def income_color(transaction_type):
    """Return Bootstrap text-color class for income/expense."""
    return 'text-success' if transaction_type == 'income' else 'text-danger'


@register.filter
def sign_prefix(transaction_type):
    """Return + or - sign prefix for a transaction."""
    return '+' if transaction_type == 'income' else '-'


@register.simple_tag
def budget_bar_width(budget):
    """Return capped percentage for progress bar width."""
    return min(budget.percentage_used, 100)


@register.filter
def month_name(month_number):
    """Convert a month number (1-12) to its full name."""
    import calendar
    try:
        return calendar.month_name[int(month_number)]
    except (ValueError, IndexError):
        return ''


@register.filter
def dict_get(dictionary, key):
    """Get a value from a dict by key in a template."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''
