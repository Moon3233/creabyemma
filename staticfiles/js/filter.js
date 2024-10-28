let activeCategory = null;  // Variable pour suivre la catégorie active

// Fonction pour trier les vêtements par catégorie
document.querySelectorAll('.category-button').forEach(function(button) {
    button.addEventListener('click', function() {
        const selectedCategory = this.getAttribute('data-categorie');  // Récupère l'ID de la catégorie du bouton cliqué
        const vetements = document.querySelectorAll('.grid-item');  // Récupère tous les vêtements

        // Si la catégorie cliquée est déjà active, réinitialiser et afficher tout
        if (activeCategory === selectedCategory) {
            vetements.forEach(function(vetement) {
                vetement.style.display = 'flex';  // Affiche tous les vêtements
            });
            activeCategory = null;  // Réinitialise la catégorie active
            // Retirer la classe active des boutons
            document.querySelectorAll('.category-button').forEach(function(btn) {
                btn.classList.remove('active');
            });
        } else {
            // Sinon, filtrer selon la nouvelle catégorie
            vetements.forEach(function(vetement) {
                const vetementCategory = vetement.getAttribute('data-categorie');  // Récupère l'ID de la catégorie du vêtement
                if (selectedCategory === vetementCategory || selectedCategory === "all") {
                    vetement.style.display = 'flex';  // Affiche le vêtement s'il correspond à la catégorie
                } else {
                    vetement.style.display = 'none';  // Cache le vêtement s'il ne correspond pas
                }
            });

            // Met à jour la catégorie active
            activeCategory = selectedCategory;
            
            // Ajouter la classe active au bouton cliqué
            document.querySelectorAll('.category-button').forEach(function(btn) {
                btn.classList.remove('active');  // Retire la classe active de tous les boutons
            });
            this.classList.add('active');  // Ajoute la classe active au bouton actuel
        }
    });
});
