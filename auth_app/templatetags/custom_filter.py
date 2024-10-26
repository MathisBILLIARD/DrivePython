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
        return f"{file_size / 1000:.2f} ko"  # Divise par 1024 et garde 2 chiffres significatifs
    else:
        return f"{file_size / 1000000:.2f} Mo"  # Divise par 1048576 et garde 2 chiffres significatifs

@register.filter
def foldername_display(folder_path):
    """
    Extrait le nom du dossier à partir du chemin complet.
    """
    return folder_path.split('/')[-2]

@register.filter
def sum_files_size(files):
    """
    Calcule la taille totale des fichiers.
    """
    return sum([file.file_size for file in files])

@register.filter
def usage_percentage(file_size, max_size=100 * 1024 * 1024):  # Par défaut, 100 Mo en octets
    """
    Calcule le pourcentage d'utilisation par rapport à la taille max.
    """
    percentage = (file_size / max_size) * 100
    return round(min(percentage, 100), 2)  # Limite à 100 % max et arrondi à 2 décimales