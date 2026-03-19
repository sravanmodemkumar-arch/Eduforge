"""Custom template tags and filters for the Portal service."""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def htmx_fragment(context, fragment_name=""):
    """Return True if the current request is an HTMX request.

    Usage in templates::

        {% load portal_tags %}
        {% htmx_fragment as is_htmx %}
        {% if is_htmx %}
            {# render only the fragment #}
        {% endif %}
    """
    request = context.get("request")
    if request and hasattr(request, "htmx"):
        return bool(request.htmx)
    return False


@register.filter(name="currency_inr")
def currency_inr(value):
    """Format a numeric value as Indian Rupees: Rs. X,XX,XXX.XX

    The Indian numbering system groups the last three digits, then every two
    digits thereafter.  For example 1234567 becomes 12,34,567.

    Usage::

        {{ amount|currency_inr }}
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    is_negative = value < 0
    value = abs(value)

    # Split integer and decimal parts
    integer_part = int(value)
    decimal_part = round(value - integer_part, 2)
    decimal_str = f"{decimal_part:.2f}"[1:]  # ".XX"

    # Format with Indian grouping
    s = str(integer_part)
    if len(s) <= 3:
        formatted = s
    else:
        # Last 3 digits
        last3 = s[-3:]
        remaining = s[:-3]
        # Group remaining in pairs from right
        groups = []
        while remaining:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        groups.reverse()
        formatted = ",".join(groups) + "," + last3

    sign = "-" if is_negative else ""
    return mark_safe(f"{sign}\u20b9{formatted}{decimal_str}")
