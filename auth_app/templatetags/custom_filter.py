# Dans le fichier yourapp/templatetags/custom_filters.py
import os
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
    return os.path.basename(os.path.dirname(folder_path))
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

@register.filter
def number_file_in_folder(files, folder):
    """
    Compte le nombre de fichiers dans un dossier.
    """
    number = len([file for file in files if (file.file_path).startswith(folder.folder_path + "/")])
    # fichier ou fichiers
    return f"{number} fichier{'s' if number > 1 else ''}"

@register.filter
def folder_name(folder_path):
    """
    Extrait le nom du dossier à partir du chemin complet.
    """
    return os.path.basename(folder_path)
