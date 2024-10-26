from django.db import models
import os
from django.conf import settings
from pillow_avif import AvifImagePlugin #Nécessaire

class Catégorie(models.Model):
    nom = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='media/logos/')

    def __str__(self):
        return self.nom

class Vêtement(models.Model):
    nom = models.CharField(max_length=100, null=True)
    image = models.ImageField(upload_to='media/images/')
    categorie = models.ForeignKey(Catégorie, on_delete=models.CASCADE, related_name='vetements')

    def __str__(self):
        return self.nom

    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)  # Supprime le fichier image du système de fichiers
        super(Vêtement, self).delete(*args, **kwargs)