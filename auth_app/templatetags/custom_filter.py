# Dans le fichier yourapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def filesize_display(file_size, unit=''):
    """
    Divise file_size par la bonne unité et garde trois chiffres.
    """
    if file_size < 1024:
        return f"{file_size} octets"
    elif file_size < 1048576:
        return f"{round(file_size / 1000)} ko"  # Divise par 1024 et garde 2 chiffres significatifs
    else:
        return f"{round(file_size / 1000000)} Mo"  # Divise par 1048576 et garde 2 chiffres significatifs
