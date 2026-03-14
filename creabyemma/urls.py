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
from pathlib import Path
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from . import views

# Racine du build Svelte (frontend/dist)
SPA_ROOT = Path(settings.BASE_DIR) / 'frontend' / 'dist'

urlpatterns = [
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path('admin/', admin.site.urls),

    # API et endpoints Django
    path('filter/', views.filter_vetements, name='filter_vetements'),
    path('upload/', views.upload_images, name='upload_images'),
    path('update_vetement_name/<int:vetement_id>/', views.update_vetement_name, name='update_vetement_name'),
    path('delete_vetement_image/<int:vetement_id>/', views.delete_vetement_image, name='delete_vetement_image'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/vetements/', views.api_vetements, name='api_vetements'),
    path('api/auth/status/', views.api_auth_status, name='api_auth_status'),
    path('api/chat/', include('chat.urls')),
    path('login/', views.login_view, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('logout', views.custom_logout),  # sans slash (bouton Déconnexion)

    # Assets SPA (JS, CSS depuis frontend/dist/assets)
    re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': SPA_ROOT / 'assets'}),
    path('favicon.svg', lambda r: serve(r, 'favicon.svg', document_root=SPA_ROOT)),
    path('icons.svg', lambda r: serve(r, 'icons.svg', document_root=SPA_ROOT)),

    # Routes SPA (fallback : sert index.html)
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('contact', views.contact),
    path('gestion/', views.home, name='gestion_spa'),
    path('gestion', views.home),
    path('login', views.login_view),  # /login sans slash (SPA)
    re_path(r'^.*$', views.home),  # catch-all pour les autres routes SPA
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

