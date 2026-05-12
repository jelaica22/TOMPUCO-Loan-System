# main/templatetags/safe_url.py
from django import template

register = template.Library()

@register.simple_tag
def file_url(file_field, default='#'):
    """Safely get file URL or return default if file doesn't exist"""
    if file_field:
        try:
            # Try to access the URL
            url = file_field.url
            if url:
                return url
        except (ValueError, AttributeError, OSError):
            pass
    return default