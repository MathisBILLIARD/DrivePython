from django.contrib import admin
from django.urls import path
from auth_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('accueil/', views.acceuil, name='accueil'),
    path('trash/', views.trash, name='trash'),
    path('favorites/', views.favorites, name='favorites'),
    path('statistics/', views.statistics, name='statistics'),
    path('recents/', views.recents, name='recents'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('upload_file/', views.upload_file, name='upload_file'),
    path('upload_file_in_folder/<str:folder_name>/', views.upload_file_in_folder, name='upload_file_in_folder'),
    path('user_files/', views.user_files, name='user_files'),
    path('upload_folder/', views.upload_folder, name='upload_folder'),
    path('create_folder/<str:folder_name>/', views.create_folder, name='create_folder'),
    path('display_folder/<str:folder_name>/', views.display_folder, name='display_folder'),
    path('trash_file/<int:file_id>/', views.trash_file, name='trash_file'),
    path('trash_folder/<int:folder_id>/', views.trash_folder, name='trash_folder'),
    path('restore_file/<int:file_id>/', views.restore_file, name='restore_file'),
    path('restore_folder/<int:folder_id>/', views.restore_folder, name='restore_folder'),
    path('delete_file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('delete_folder/<int:folder_id>/', views.delete_folder, name='delete_folder'),
    path('rename_file/<int:file_id>/<str:new_name>/', views.rename_file, name='rename_file'),
    path('rename_folder/<int:folder_id>/<str:new_name>/', views.rename_folder, name='rename_folder'),
    path('add_favorite/<int:file_id>/', views.add_favorite, name='add_favorite'),
    path('remove_favorite/<int:file_id>/', views.remove_favorite, name='remove_favorite'),
    path('add_favorite_folder/<int:folder_id>/', views.add_favorite_folder, name='add_favorite_folder'),
    path('remove_favorite_folder/<int:folder_id>/', views.remove_favorite_folder, name='remove_favorite_folder'),
    path('style/', views.style, name='style'),

]