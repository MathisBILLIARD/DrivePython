from django.db import models
from django.contrib.auth.models import User  # Utilisation du modèle User par défaut

class Utilisateur(models.Model):
    nom = models.CharField(max_length=50)
    mot_de_passe = models.CharField(max_length=50)

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Association avec l'utilisateur
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)  # Chemin du fichier stocké
    file_size = models.IntegerField(default=0)  # Taille du fichier en octets
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} (Uploaded by {self.user.username})"


class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Association avec l'utilisateur
    folder_name = models.CharField(max_length=255)
    folder_path = models.CharField(max_length=255)  # Chemin du dossier stocké
    upload_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.folder_name} (Uploaded by {self.user.username})"
