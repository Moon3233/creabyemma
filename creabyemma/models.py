from django.db import models
from pillow_avif import AvifImagePlugin #Nécessaire
from storages.backends.s3boto3 import S3Boto3Storage

class Catégorie(models.Model):
    nom = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/', storage=S3Boto3Storage(), default="")

    def __str__(self):
        return self.nom

class Vêtement(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='images/', storage=S3Boto3Storage())  # Spécifier explicitement le stockage S3
    categorie = models.ForeignKey('Catégorie', on_delete=models.CASCADE, related_name='vetements')

    def __str__(self):
        return self.nom if self.nom else "Sans nom"