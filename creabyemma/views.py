from django.shortcuts import render, redirect, get_object_or_404
from .models import Vêtement, Catégorie
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponse
import json

import os
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import uuid

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /login/"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def home(request):
    categorie_id = request.GET.get('categorie')  # Récupère l'ID de la catégorie sélectionnée
    categories = Catégorie.objects.all()  # Récupère toutes les catégories

    if categorie_id:  # Si une catégorie est sélectionnée
        vetements = Vêtement.objects.filter(categorie_id=categorie_id)  # Filtrer les vêtements par catégorie
    else:
        vetements = Vêtement.objects.all()  # Sinon, afficher tous les vêtements

    return render(request, 'pages/home.html', {'vetements': vetements, 'categories': categories})

def filter_vetements(request):
    categorie_id = request.GET.get('categorie')
    if categorie_id:
        vetements = Vêtement.objects.filter(categorie_id=categorie_id)
    else:
        vetements = Vêtement.objects.all()

    vetement_data = [
        {
            'nom': vetement.nom,
            'image_url': vetement.image.url,
            'categorie': vetement.categorie.nom
        } for vetement in vetements
    ]

    return JsonResponse({'vetements': vetement_data})

@login_required
def upload_images(request):
    if request.method == 'POST':
        categorie_id = request.POST.get('categorie')
        categorie = Catégorie.objects.get(id=categorie_id)

        images = request.FILES.getlist('image')
        for image in images:
            # Directement sauvegarder l'image sans conversion
            vetement = Vêtement(categorie=categorie)
            vetement.image.save(image.name, image)
            vetement.save()

        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


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
    return render(request, 'pages/contact.html')