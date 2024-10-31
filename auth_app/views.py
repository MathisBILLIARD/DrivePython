import shutil
from django.shortcuts import render, redirect, get_object_or_404
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
    display_folders = [folder for folder in user_folders if os.path.basename(os.path.dirname(folder.folder_path)) not in [folder.folder_name for folder in user_folders]]
    # Récupère tous les fichiers uploades n'étant pas dans les dossiers uploadés par l'utilisateur connecté n'étant pas dans la corbeille
    user_files = UploadedFile.objects.filter(user=request.user, trash=False)
    # files not in user_folders
    files_not_folder = [file for file in user_files if os.path.basename(os.path.dirname(file.file_path)) not in [folder.folder_name for folder in user_folders]]
    return render(request, 'accueil.html', {'files': user_files, 'folders': display_folders, 'files_not_folder': files_not_folder, 'all_user_files': all_user_files})

def display_folder(request, folder_id):
    # Récupérer les fichiers de l'utilisateur dans le dossier spécifié
    folderMain = Folder.objects.get(id=folder_id)
    user_files = UploadedFile.objects.filter(user=request.user, trash=False)
    folder_files = [
        file for file in user_files
        if os.path.dirname(file.file_path) == folderMain.folder_path
    ]
    # Récupérer les dossiers dans le dossier spécifié
    user_folders = Folder.objects.filter(user=request.user, trash=False)
    folder_folders = [
        folder for folder in user_folders
        if os.path.basename(os.path.dirname(folder.folder_path)) == os.path.basename(folderMain.folder_path)
    ]

    # Passer `folder_name` directement si vous n'avez pas d'objet `Folder` pour le dossier
    return render(request, 'folder_files.html', {'files': user_files, 'folder_files': folder_files, 'folder_name': folderMain.folder_name, 'folder_id':folder_id, 'all_user_files': user_files, 'folders': folder_folders})

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

def upload_file_in_folder(request, folder_id):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']  # Récupère le fichier uploadé
        folder = Folder.objects.get(id=folder_id)
        folder_name = folder.folder_name
        # Vérifier si la somme des tailles des fichiers de l'utilisateur plus le fichier uploader dépasse la limite de 100 Mo
        user_files = UploadedFile.objects.filter(user=request.user)
        total_size = sum([file.file_size for file in user_files]) + uploaded_file.size
        if total_size > 100 * 1000 * 1000:  # 100 Mo en octets
            messages.error(request, 'La taille totale de vos fichiers dépasse la limite autorisée.')
            return redirect('accueil')

        # Définir le chemin du dossier de destination (par exemple : media/uploads/user_<id>/)
        pathFolder = folder.folder_path
        destination_folder = os.path.join(settings.MEDIA_ROOT, pathFolder)
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
        return redirect('display_folder', folder_id)     

    
    return redirect('display_folder', folder_id)

def upload_folder_in_folder(request, folder_id):
    if request.method == 'POST' and request.FILES.getlist('files'):
        files = request.FILES.getlist('files')  # Récupère tous les fichiers uploadés
        new_folder_name = request.POST.get('folder_name')  # Récupère le nom du dossier
        # Vérifier si la somme des tailles des fichiers de l'utilisateur plus la taille des fichiers uploader dépasse la limite de 100 Mo
        user_files = UploadedFile.objects.filter(user=request.user)
        folder = Folder.objects.get(id=folder_id)
        folder_name = folder.folder_name
        total_size = sum([file.file_size for file in user_files]) + sum([file.size for file in files])
        if total_size > 100 * 1000 * 1000:  # 100 Mo en octets
            messages.error(request, 'La taille totale de vos fichiers dépasse la limite autorisée.')
            return redirect('accueil')
        # Définir le dossier utilisateur
        user_folder = f'user_{request.user.id}'
        # On récupère lesd dossiers dans le dossier spécifié
        user_folders = Folder.objects.filter(user=request.user)
        folder_folders = [
            folder for folder in user_folders
            if os.path.basename(os.path.dirname(folder.folder_path)) == folder_name
        ]
        # Si le dossier existe déjà dans folder_folders, on ajoute un numéro à la fin
        if new_folder_name in [folder.folder_name for folder in folder_folders]:
            folder_name1, folder_extension = os.path.splitext(new_folder_name)
            i = 1
            while new_folder_name in [folder.folder_name for folder in folder_folders]:
                new_folder_name = f'{folder_name1}_{i}'
                i += 1
        path_Folder = folder.folder_path
        base_destination_folder = os.path.join(settings.MEDIA_ROOT, path_Folder, new_folder_name)
        folder_destination = os.path.join(settings.MEDIA_ROOT, path_Folder, new_folder_name)
        # Créer le dossier de destination
        os.makedirs(base_destination_folder, exist_ok=True)
        uploaded_folder_instance = Folder(
                user=request.user,
                folder_name=new_folder_name,
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

            # Sauvegarde dans la base de données
            uploaded_file_instance = UploadedFile(
                user=request.user,
                file_name=uploaded_file.name,
                file_path=file_path,
                file_size=uploaded_file.size
            )
            uploaded_file_instance.save()

        # Redirection ou message de succès
        return redirect('display_folder', folder_id)
    
    return redirect('display_folder', folder_id)


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
    folder = get_object_or_404(Folder, id=folder_id)
    
    # Vérifier si un dossier avec le nouveau nom existe déjà pour l'utilisateur
    if Folder.objects.filter(user=request.user, folder_name=new_name).exists():
        # Ajouter un numéro à la fin du nom pour éviter les duplicatas
        folder_name_base, folder_extension = os.path.splitext(new_name)
        i = 1
        while Folder.objects.filter(user=request.user, folder_name=new_name).exists():
            new_name = f'{folder_name_base}_{i}'
            i += 1

    # Renommer le dossier et mettre à jour le champ `folder_name`
    old_folder_path = folder.folder_path
    dirpath = os.path.dirname(old_folder_path)
    new_folder_path = os.path.join(settings.MEDIA_ROOT, dirpath, new_name)
    os.rename(old_folder_path, new_folder_path)  # Renommer le dossier sur le système de fichiers
    folder.folder_name = new_name
    folder.folder_path = new_folder_path
    folder.save()

    # Mettre à jour tous les fichiers dans le dossier
    update_file_paths(folder, old_folder_path, new_folder_path)

    # Mettre à jour récursivement les sous-dossiers et leurs fichiers
    update_subfolder_paths(folder, old_folder_path, new_folder_path, request.user)

    return redirect('accueil')

def update_file_paths(folder, old_folder_path, new_folder_path):
    """
    Met à jour les chemins de tous les fichiers dans le dossier donné.
    """
    folder_files = UploadedFile.objects.filter(user=folder.user, file_path__startswith=old_folder_path)
    for file in folder_files:
        # Modifier le chemin du fichier
        new_file_path = file.file_path.replace(old_folder_path, new_folder_path, 1)
        file.file_path = new_file_path
        file.save()

def update_subfolder_paths(folder, old_folder_path, new_folder_path, user):
    """
    Met à jour les chemins des sous-dossiers et de leurs fichiers de manière récursive.
    """
    subfolders = Folder.objects.filter(user=user, folder_path__startswith=old_folder_path).exclude(id=folder.id)
    for subfolder in subfolders:
        # Nouveau chemin du sous-dossier
        new_subfolder_path = subfolder.folder_path.replace(old_folder_path, new_folder_path, 1)

        # Mettre à jour le chemin dans la base de données
        subfolder.folder_path = new_subfolder_path
        subfolder.save()

        # Mettre à jour les chemins des fichiers dans le sous-dossier
        update_file_paths(subfolder, subfolder.folder_path, new_subfolder_path)

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
    
    # Ajouter tous les dossiers dans le dossier aux favoris
    user_folders = Folder.objects.filter(user=request.user)
    folder_folders = [
        folder1 for folder1 in user_folders
        if os.path.dirname(folder1.folder_path) == folder.folder_path
    ]
    for folder1 in folder_folders:
        add_favorite_folder(request, folder1.id)
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
    
    # Retirer tous les dossiers dans le dossier des favoris
    user_folders = Folder.objects.filter(user=request.user)
    folder_folders = [
        folder1 for folder1 in user_folders
        if os.path.dirname(folder1.folder_path) == folder.folder_path
    ]
    for folder1 in folder_folders:
        remove_favorite_folder(request, folder1.id)
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
    
    # Mettre tous les dossiers dans le dossier dans la corbeille
    user_folders = Folder.objects.filter(user=request.user)
    folder_folders = [
        folder1 for folder1 in user_folders
        if os.path.dirname(folder1.folder_path) == folder.folder_path
    ]
    for folder1 in folder_folders:
        trash_folder(request, folder1.id)
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
    # Restaurer tous les dossiers dans le dossier
    user_folders = Folder.objects.filter(user=request.user)
    folder_folders = [
        folder1 for folder1 in user_folders
        if os.path.dirname(folder1.folder_path) == folder.folder_path
    ]
    for folder1 in folder_folders:
        restore_folder(request, folder1.id)
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

def create_folder_in_folder(request, folder_id, folder_name):
    # Vérifier si le dossier existe déjà
    if Folder.objects.filter(user=request.user, folder_name=folder_name).exists():
        # on ajouter un numéro à la fin du nom du dossier
        folder_name1, folder_extension = os.path.splitext(folder_name)
        i = 1
        while Folder.objects.filter(user=request.user, folder_name=folder_name).exists():
            folder_name = f'{folder_name1}_{i}'
            i += 1
    # Créer le dossier
    folder = Folder.objects.get(id=folder_id)
    pathFolder = folder.folder_path
    destination_folder = os.path.join(settings.MEDIA_ROOT, pathFolder, folder_name)
    os.makedirs(destination_folder, exist_ok=True)
    uploaded_folder_instance = Folder(
        user=request.user,
        folder_name=folder_name,
        folder_path=destination_folder
    )
    uploaded_folder_instance.save()
    return redirect('display_folder', folder_id)

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
    # supprimer tous les dossiers dans le dossier
    user_folders = Folder.objects.filter(user=request.user)
    folder_folders = [
        folder1 for folder1 in user_folders
        if os.path.dirname(folder1.folder_path) == folder.folder_path
    ]
    for folder1 in folder_folders:
        delete_folder(request, folder1.id)
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
    display_folders = [folder for folder in user_folders if os.path.basename(os.path.dirname(folder.folder_path)) not in [folder.folder_name for folder in user_folders]]
    files_not_folder = [file for file in user_files if os.path.basename(os.path.dirname(file.file_path)) not in [folder.folder_name for folder in user_folders]]
    return render(request, 'trash.html', {'files': user_files, 'folders': display_folders, 'files_not_folder': files_not_folder, 'all_user_files': all_user_files})

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
    display_folders = [folder for folder in user_folders if os.path.basename(os.path.dirname(folder.folder_path)) not in [folder.folder_name for folder in user_folders]]
    files_not_folder = [file for file in user_files if os.path.basename(os.path.dirname(file.file_path)) not in [folder.folder_name for folder in user_folders]]
    return render(request, 'favorites.html', {'files': user_files, 'folders': display_folders, 'files_not_folder': files_not_folder, 'all_user_files': all_user_files})

def user_files(request):
    # Récupère tous les fichiers uploadés par l'utilisateur connecté
    user_files = UploadedFile.objects.filter(user=request.user)
    
    return render(request, 'user_files.html', {'files': user_files})
