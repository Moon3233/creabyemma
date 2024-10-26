import logging
from django.db import models
from django.core.files import File

# Configuration des logs pour le module
logger = logging.getLogger(__name__)

class Catégorie(models.Model):
    nom = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/', default="")

    def save(self, *args, **kwargs):
        logger.debug(f"Tentative de sauvegarde de Catégorie : {self.nom}")
        
        # Suivi du fichier avant l'upload
        if self.logo:
            logger.debug(f"Préparation de l'upload du logo : {self.logo.name}")
        
        # Appel de la méthode save de la superclasse
        super().save(*args, **kwargs)
        
        # Vérification de l'upload réussi
        if self.logo:
            logger.debug(f"Logo uploadé avec succès : {self.logo.url}")

    def __str__(self):
        return self.nom


class Vêtement(models.Model):
    nom = models.CharField(max_length=100, null=True)
    image = models.ImageField(upload_to='images/')
    categorie = models.ForeignKey(Catégorie, on_delete=models.CASCADE, related_name='vetements')

    def save(self, *args, **kwargs):
        logger.debug(f"Tentative de sauvegarde de Vêtement : {self.nom}")
        
        # Suivi du fichier avant l'upload
        if self.image:
            logger.debug(f"Préparation de l'upload de l'image : {self.image.name}")
        
        # Appel de la méthode save de la superclasse
        super().save(*args, **kwargs)
        
        # Vérification de l'upload réussi
        if self.image:
            logger.debug(f"Image uploadée avec succès : {self.image.url}")

    def __str__(self):
        return self.nom
