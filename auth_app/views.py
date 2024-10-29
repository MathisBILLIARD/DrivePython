import shutil
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm 
from .form import CustomUserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import os
from django.conf import settings
from django.core.files.storage import default_storage
from .models import UploadedFile, Folder

# Create your views here.
def inscription(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('connexion')
    else:
        form = CustomUserCreationForm()
    return render(request, 'inscription.html', {'form': form})

def connexion(request):
    print("Je suis appelé")
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('accueil')
        else:
            messages.error(request, 'Incorrect username or password.')
    return render(request, 'connexion.html')

@login_required
def acceuil(request):
    all_user_files = UploadedFile.objects.filter(user=request.user)
    # Récupère tous  les dossiers uploadés par l'utilisateur connecté n'étant pas dans la corbeille
    user_folders = Folder.objects.filter(user=request.user, trash=False)
    # Récupère tous les fichiers uploades n'étant pas dans les dossiers uploadés par l'utilisateur connecté n'étant pas dans la corbeille
    user_files = UploadedFile.objects.filter(user=request.user, trash=False)
    # files not in user_folders
    files_not_folder = [file for file in user_files if os.path.basename(os.path.dirname(file.file_path)) not in [folder.folder_name for folder in user_folders]]
    return render(request, 'accueil.html', {'files': user_files, 'folders': user_folders, 'files_not_folder': files_not_folder, 'all_user_files': all_user_files})

def display_folder(request, folder_name):
    # Récupérer les fichiers de l'utilisateur dans le dossier spécifié
    user_files = UploadedFile.objects.filter(user=request.user)
    folder_files = [
        file for file in user_files
        if os.path.basename(os.path.dirname(file.file_path)) == folder_name
    ]

    # Passer `folder_name` directement si vous n'avez pas d'objet `Folder`
    return render(request, 'folder_files.html', {'files': folder_files, 'folder_name': folder_name, 'all_user_files': user_files})

def deconnexion(request):
    logout(request)
    return redirect('connexion')

def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']  # Récupère le fichier uploadé
        # Vérifier si la somme des tailles des fichiers de l'utilisateur plus le fichier uploader dépasse la limite de 100 Mo
        user_files = UploadedFile.objects.filter(user=request.user)
        total_size = sum([file.file_size for file in user_files]) + uploaded_file.size
        if total_size > 100 * 1000 * 1000:  # 100 Mo en octets
            messages.error(request, 'La taille totale de vos fichiers dépasse la limite autorisée.')
            return redirect('accueil')

        # Définir le chemin du dossier de destination (par exemple : media/uploads/user_<id>/)
        user_folder = f'user_{request.user.id}'
        destination_folder = os.path.join(settings.MEDIA_ROOT, 'uploads', user_folder)
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Vérifier si le fichier existe déjà
        if UploadedFile.objects.filter(user=request.user, file_name=uploaded_file.name).exists():
            # on ajouter un numéro à la fin du nom du fichier
            file_name, file_extension = os.path.splitext(uploaded_file.name)
            i = 1
            while UploadedFile.objects.filter(user=request.user, file_name=uploaded_file.name).exists():
                uploaded_file.name = f'{file_name}_{i}{file_extension}'
                i += 1

        # Chemin de sauvegarde complet pour le fichier
        file_path = os.path.join(destination_folder, uploaded_file.name)

        # Enregistre le fichier sur le serveur
        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Sauvegarde du fichier dans la base de données avec l'utilisateur
        uploaded_file_instance = UploadedFile(
            user=request.user, 
            file_name=uploaded_file.name, 
            file_path=file_path,
            file_size=uploaded_file.size
        )
        uploaded_file_instance.save()
        user_files = UploadedFile.objects.filter(user=request.user)

        # lien vers la fonction accueil
        # Redirection ou message de succès
        return redirect('accueil')        

    return redirect('accueil') 

def upload_folder(request):
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')  # Récupère tous les fichiers uploadés
        folder_name = request.POST.get('folder_name')  # Récupère le nom du dossier
        # Vérifier si la somme des tailles des fichiers de l'utilisateur plus la taille des fichiers uploader dépasse la limite de 100 Mo
        user_files = UploadedFile.objects.filter(user=request.user)
        total_size = sum([file.file_size for file in user_files]) + sum([file.size for file in files])
        if total_size > 100 * 1000 * 1000:  # 100 Mo en octets
            messages.error(request, 'La taille totale de vos fichiers dépasse la limite autorisée.')
            return redirect('accueil')
        # Définir le dossier utilisateur
        user_folder = f'user_{request.user.id}'
        # Si le dossier existe déjà, on ajoute un numéro à la fin
        if Folder.objects.filter(user=request.user, folder_name=folder_name).exists():
            folder_name1, folder_extension = os.path.splitext(folder_name)
            i = 1
            while Folder.objects.filter(user=request.user, folder_name=folder_name).exists():
                folder_name = f'{folder_name1}_{i}'
                i += 1
        base_destination_folder = os.path.join(settings.MEDIA_ROOT, 'uploads', user_folder, folder_name)
        folder_destination = os.path.join(settings.MEDIA_ROOT, 'uploads', user_folder, folder_name)

        # Créer le dossier de destination
        os.makedirs(base_destination_folder, exist_ok=True)
        uploaded_folder_instance = Folder(
                user=request.user,
                folder_name=folder_name,
                folder_path=folder_destination
            )
        uploaded_folder_instance.save()
        # Parcours chaque fichier uploadé
        for uploaded_file in files:
            # Chemin de sauvegarde complet pour chaque fichier
            file_path = os.path.join(base_destination_folder, uploaded_file.name)

            # Enregistre le fichier sur le serveur
            with default_storage.open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Sauvegarde dans la base de données si nécessaire
            uploaded_file_instance = UploadedFile(
                user=request.user,
                file_name=uploaded_file.name,
                file_path=file_path,
                file_size=uploaded_file.size
            )
            uploaded_file_instance.save()

        # Redirection ou message de succès
        return redirect('accueil')

    return redirect('accueil')

def rename_file(request, file_id, new_name):
    # Récupère le fichier à renommer
    file = UploadedFile.objects.get(id=file_id)
    # Récupère l'extension du fichier
    file_name, file_extension = os.path.splitext(file.file_name)
    new_name = f'{new_name}{file_extension}'
    # Vérifier si le fichier existe déjà
    if UploadedFile.objects.filter(user=request.user, file_name=new_name).exists():
        # on ajouter un numéro à la fin du nom du fichier
        file_name, file_extension = os.path.splitext(new_name)
        i = 1
        while UploadedFile.objects.filter(user=request.user, file_name=new_name).exists():
            new_name = f'{file_name}_{i}{file_extension}'
            i += 1
    # Renommer le fichier sur le serveur
    old_file_path = file.file_path
    new_file_path = os.path.join(os.path.dirname(old_file_path), new_name)
    os.rename(old_file_path, new_file_path)
    # Renommer le fichier
    file.file_name = new_name
    file.file_path = new_file_path
    file.save()
    return redirect('accueil')

def rename_folder(request, folder_id, new_name):
    # Récupère le dossier à renommer
    folder = Folder.objects.get(id=folder_id)
    # Vérifier si le dossier existe déjà
    if Folder.objects.filter(user=request.user, folder_name=new_name).exists():
        # on ajouter un numéro à la fin du nom du dossier
        folder_name, folder_extension = os.path.splitext(new_name)
        i = 1
        while Folder.objects.filter(user=request.user, folder_name=new_name).exists():
            new_name = f'{folder_name}_{i}'
            i += 1
    # Modifier le path des fichiers du dossier
    user_files = UploadedFile.objects.filter(user=request.user)
    folder_files = [
        file for file in user_files
        if os.path.basename(os.path.dirname(file.file_path)) == folder.folder_name
    ]
    # Renommer le dossier
    folder.folder_name = new_name
    # Renommer le dossier sur le serveur
    old_folder_path = folder.folder_path
    new_folder_path = os.path.join(settings.MEDIA_ROOT, 'uploads', f'user_{request.user.id}', new_name)
    os.rename(old_folder_path, new_folder_path)
    for file in folder_files:
        file_path = file.file_path
        new_file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', f'user_{request.user.id}', new_name, os.path.basename(file_path))
        file.file_path = new_file_path
        file.save()
    folder.folder_path = new_folder_path
    folder.save()
    return redirect('accueil')

def add_favorite(request, file_id):
    # Récupère le fichier à ajouter aux favoris
    file = UploadedFile.objects.get(id=file_id)
    file.favorite = True
    file.save()
    return redirect('accueil')

def remove_favorite(request, file_id):
    # Récupère le fichier à retirer des favoris
    file = UploadedFile.objects.get(id=file_id)
    file.favorite = False
    file.save()
    return redirect('accueil')

def add_favorite_folder(request, folder_id):
    # Récupère le dossier à ajouter aux favoris
    folder = Folder.objects.get(id=folder_id)
    folder.favorite = True
    # Ajouter tous les fichiers du dossier aux favoris
    user_files = UploadedFile.objects.filter(user=request.user)
    folder_files = [
        file for file in user_files
        if os.path.basename(os.path.dirname(file.file_path)) == folder.folder_name
    ]
    for file in folder_files:
        file.favorite = True
        file.save()
    folder.save()
    return redirect('accueil')

def remove_favorite_folder(request, folder_id):
    # Récupère le dossier à retirer des favoris
    folder = Folder.objects.get(id=folder_id)
    folder.favorite = False
    # Retirer tous les fichiers du dossier des favoris
    user_files = UploadedFile.objects.filter(user=request.user)
    folder_files = [
        file for file in user_files
        if os.path.basename(os.path.dirname(file.file_path)) == folder.folder_name
    ]
    for file in folder_files:
        file.favorite = False
        file.save()
    folder.save()
    return redirect('accueil')


def trash_file(request, file_id):
    # Récupère le fichier à mettre dans la corbeille
    file = UploadedFile.objects.get(id=file_id)
    file.trash = True
    file.favorite = False
    file.save()
    return redirect('accueil')

def trash_folder(request, folder_id):
    # Récupère le dossier à mettre dans la corbeille
    folder = Folder.objects.get(id=folder_id)
    folder.trash = True
    folder.favorite = False
    # Mettre tous les fichiers du dossier dans la corbeille
    user_files = UploadedFile.objects.filter(user=request.user)
    folder_files = [
        file for file in user_files
        if os.path.basename(os.path.dirname(file.file_path)) == folder.folder_name
    ]
    for file in folder_files:
        file.trash = True
        file.favorite = False
        file.save()
    folder.save()
    return redirect('accueil')

def restore_file(request, file_id):
    # Récupère le fichier à restaurer
    file = UploadedFile.objects.get(id=file_id)
    file.trash = False
    file.save()
    return redirect('accueil')

def restore_folder(request, folder_id):
    # Récupère le dossier à restaurer
    folder = Folder.objects.get(id=folder_id)
    folder.trash = False
    # Restaurer tous les fichiers du dossier
    user_files = UploadedFile.objects.filter(user=request.user)
    folder_files = [
        file for file in user_files
        if os.path.basename(os.path.dirname(file.file_path)) == folder.folder_name
    ]
    for file in folder_files:
        file.trash = False
        file.save()
    folder.save()
    return redirect('accueil')

def create_folder(request, folder_name):
    # Vérifier si le dossier existe déjà
    if Folder.objects.filter(user=request.user, folder_name=folder_name).exists():
        # on ajouter un numéro à la fin du nom du dossier
        folder_name1, folder_extension = os.path.splitext(folder_name)
        i = 1
        while Folder.objects.filter(user=request.user, folder_name=folder_name).exists():
            folder_name = f'{folder_name1}_{i}'
            i += 1
    # Créer le dossier
    user_folder = f'user_{request.user.id}'
    destination_folder = os.path.join(settings.MEDIA_ROOT, 'uploads', user_folder, folder_name)
    os.makedirs(destination_folder, exist_ok=True)
    uploaded_folder_instance = Folder(
        user=request.user,
        folder_name=folder_name,
        folder_path=destination_folder
    )
    uploaded_folder_instance.save()
    return redirect('accueil')

def delete_file(request, file_id):
    # Récupère le fichier à supprimer
    file = UploadedFile.objects.get(id=file_id)
    file.delete()
    # Supprimer le fichier du serveur
    os.remove(file.file_path)
    return redirect('accueil')

def delete_folder(request, folder_id):
    # Récupère le dossier à supprimer
    folder = Folder.objects.get(id=folder_id)
    folder.delete()
    # Supprimer tous les fichiers du dossier
    user_files = UploadedFile.objects.filter(user=request.user)
    folder_files = [
        file for file in user_files
        if os.path.basename(os.path.dirname(file.file_path)) == folder.folder_name
    ]
    for file in folder_files:
        file.delete()
    # Supprimer tout le dossier du serveur
    shutil.rmtree(folder.folder_path)
    return redirect('accueil')

def style(request):
    return render(request, 'style.css', content_type='text/css')

def trash(request):
    # Récupère tous les fichiers et les dossiers uploadés par l'utilisateur connecté dans la corbeille
    all_user_files = UploadedFile.objects.filter(user=request.user)
    user_files = UploadedFile.objects.filter(user=request.user, trash=True)
    user_folders = Folder.objects.filter(user=request.user, trash=True)
    files_not_folder = [file for file in user_files if os.path.basename(os.path.dirname(file.file_path)) not in [folder.folder_name for folder in user_folders]]
    return render(request, 'trash.html', {'files': user_files, 'folders': user_folders, 'files_not_folder': files_not_folder, 'all_user_files': all_user_files})

def recents(request):
    all_user_files = UploadedFile.objects.filter(user=request.user)
    return render(request, 'recents.html', {'all_user_files': all_user_files})

def statistics(request):
    all_user_files = UploadedFile.objects.filter(user=request.user)
    return render(request, 'statistics.html', {'all_user_files': all_user_files})

def favorites(request):
    all_user_files = UploadedFile.objects.filter(user=request.user)
    # Récupère tous les fichiers favoris de l'utilisateur connecté
    user_files = UploadedFile.objects.filter(user=request.user, favorite=True)
    user_folders = Folder.objects.filter(user=request.user, favorite=True)
    files_not_folder = [file for file in user_files if os.path.basename(os.path.dirname(file.file_path)) not in [folder.folder_name for folder in user_folders]]
    return render(request, 'favorites.html', {'files': user_files, 'folders': user_folders, 'files_not_folder': files_not_folder, 'all_user_files': all_user_files})

def user_files(request):
    # Récupère tous les fichiers uploadés par l'utilisateur connecté
    user_files = UploadedFile.objects.filter(user=request.user)
    
    return render(request, 'user_files.html', {'files': user_files})
