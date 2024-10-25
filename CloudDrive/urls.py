from django.contrib import admin
from django.urls import path
from auth_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('accueil/', views.acceuil, name='accueil'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('style/', views.style, name='style'),

]