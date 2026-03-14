from django.shortcuts import render, redirect, get_object_or_404
from .models import Vêtement, Catégorie
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.static import serve
from django.contrib.auth import authenticate, login
from pathlib import Path
import json
from django.contrib.auth import logout

import os
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import uuid

BASE_DIR = Path(settings.BASE_DIR)
SPA_ROOT = BASE_DIR / 'frontend' / 'dist'


def _serve_spa_index(request):
    """Sert l'index.html de la SPA Svelte (frontend/dist)."""
    index_path = SPA_ROOT / 'index.html'
    if not index_path.exists():
        return HttpResponse(
            '<h1>SPA non buildée</h1><p>Exécutez <code>cd frontend && npm run build</code></p>',
            status=503,
            content_type='text/html',
        )
    with open(index_path, 'r', encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='text/html')


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /login/"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def home(request):
    """Sert la SPA Svelte (page d'accueil)."""
    return _serve_spa_index(request)

def filter_vetements(request):
    categorie_id = request.GET.get('categorie')
    if categorie_id:
        vetements = Vêtement.objects.filter(categorie_id=categorie_id)
    else:
        vetements = Vêtement.objects.all()

    vetement_data = [
        {
            'id': vetement.id,
            'nom': vetement.nom if vetement.nom else "",
            'image_url': request.build_absolute_uri(vetement.image.url),
            'categorie_id': vetement.categorie_id,
            'categorie': vetement.categorie.nom,
        }
        for vetement in vetements
    ]

    return JsonResponse({'vetements': vetement_data})


def api_categories(request):
    """API : liste des catégories pour le frontend Svelte."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    categories = Catégorie.objects.all()
    data = []
    for c in categories:
        logo_url = ''
        if c.logo and getattr(c.logo, 'url', None):
            logo_url = request.build_absolute_uri(c.logo.url)
        data.append({'id': c.id, 'nom': c.nom, 'logo_url': logo_url})
    return JsonResponse({'categories': data})


def api_vetements(request):
    """API : liste des vêtements (optionnellement filtrée par catégorie)."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    categorie_id = request.GET.get('categorie')
    if categorie_id:
        vetements = Vêtement.objects.filter(categorie_id=categorie_id)
    else:
        vetements = Vêtement.objects.all()
    data = [
        {
            'id': v.id,
            'nom': v.nom or '',
            'image_url': request.build_absolute_uri(v.image.url),
            'categorie_id': v.categorie_id,
            'categorie': v.categorie.nom,
        }
        for v in vetements
    ]
    return JsonResponse({'vetements': data})


def api_auth_status(request):
    """API : indique si l'utilisateur est authentifié (pour le frontend Svelte)."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    return JsonResponse({'authenticated': request.user.is_authenticated})

@login_required
def upload_images(request):
    if request.method == 'POST':
        categorie_id = request.POST.get('categorie')
        
        categorie = Catégorie.objects.get(id=categorie_id)
        
        # Gestion de l'upload de plusieurs images
        images = request.FILES.getlist('image')
        
        # Vérifie s'il y a des images à télécharger
        if not images:
            return redirect('home')  # Retourne à la page principale si aucune image n'est sélectionnée
        
        for image in images:
            # Convertir l'image en AVIF
            avif_image = convert_to_avif(image)
            
            # Sauvegarder l'image convertie dans le modèle
            vetement = Vêtement.objects.create(categorie=categorie)
            vetement.image.save(f"{uuid.uuid4()}.avif", avif_image)

        # Réponse JSON pour le frontend Svelte (requête fetch avec credentials)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accepts('application/json'):
            return JsonResponse({'success': True})
        
        # Redirection après le succès de l'upload (fallback template Django)
        return redirect('home')
    
    # Si la requête n'est pas de type POST, retourne une erreur
    return HttpResponse("Méthode non autorisée", status=405)


def convert_to_avif(image):
    # Ouvre l'image uploadée avec Pillow
    with Image.open(image) as img:
        # Créer un buffer pour stocker l'image convertie
        buffer = BytesIO()

        # Convertir l'image en AVIF avec une qualité de 65%
        img.save(buffer, format="AVIF", quality=65)

        # Retourner l'image AVIF sous forme de fichier Django (ContentFile)
        return ContentFile(buffer.getvalue())

def update_vetement_name(request, vetement_id):
    if request.method == 'POST':
        vetement = get_object_or_404(Vêtement, id=vetement_id)
        data = json.loads(request.body)
        new_name = data.get('nom')
        if new_name:
            vetement.nom = new_name
            vetement.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Nom non fourni.'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

def delete_vetement_image(request, vetement_id):
    if request.method == 'DELETE':
        # Récupérer le vêtement et supprimer son image
        vetement = get_object_or_404(Vêtement, id=vetement_id)
        
        # Supprimer l'image
        vetement.image.delete()  # Supprime le fichier image du système de fichiers
        vetement.delete()  # Supprime le vêtement de la base de données
        
        return JsonResponse({'success': True}, status=200)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def contact(request):
    """Sert la SPA Svelte (page contact)."""
    return _serve_spa_index(request)


def login_view(request):
    """GET : sert la SPA. POST : authentification Django."""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', '/')
            return redirect(next_url)
    return _serve_spa_index(request)

def custom_logout(request):
    if request.method == 'GET' or request.method == 'POST':
        logout(request)
        return redirect('home')  # Redirige vers la page d'accueil après la déconnexion
    return HttpResponse("Méthode non autorisée", status=405)