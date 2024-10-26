from django.db import models
from pillow_avif import AvifImagePlugin #Nécessaire

class Catégorie(models.Model):
    nom = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/', default="")

    def __str__(self):
        return self.nom

class Vêtement(models.Model):
    nom = models.CharField(max_length=100, null=True)
    image = models.ImageField(upload_to='images/')
    categorie = models.ForeignKey(Catégorie, on_delete=models.CASCADE, related_name='vetements')

    def __str__(self):
        return self.nom