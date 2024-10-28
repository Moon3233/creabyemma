"""
URL configuration for creabyemma project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("robots.txt", views.robots_txt, name="robots_txt"),
    
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # Page d'accueil
    path('filter/', views.filter_vetements, name='filter_vetements'),
    path('upload/', views.upload_images, name='upload_images'),
    path('update_vetement_name/<int:vetement_id>/', views.update_vetement_name, name='update_vetement_name'),
    path('delete_vetement_image/<int:vetement_id>/', views.delete_vetement_image, name='delete_vetement_image'),

    path('contact/', views.contact, name='contact'),


    path('login/', auth_views.LoginView.as_view(template_name='pages/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

