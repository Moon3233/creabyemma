/**
 * Client API pour le backend Django.
 * Toutes les requêtes passent par le proxy Vite (dev) avec credentials.
 */

const defaults: RequestInit = {
  credentials: 'include',
  headers: { Accept: 'application/json' },
};

function getCsrfToken(): string {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (const c of cookies) {
    const [key, value] = c.trim().split('=');
    if (key === name) return decodeURIComponent(value || '');
  }
  return '';
}

export interface Categorie {
  id: number;
  nom: string;
  logo_url: string;
}

export interface Vetement {
  id: number;
  nom: string;
  image_url: string;
  categorie_id: number;
  categorie: string;
}

export async function fetchCategories(): Promise<Categorie[]> {
  const r = await fetch('/api/categories/', { ...defaults });
  if (!r.ok) throw new Error('Erreur chargement catégories');
  const data = await r.json();
  return data.categories ?? [];
}

export async function fetchVetements(categorieId?: number): Promise<Vetement[]> {
  const url = categorieId ? `/api/vetements/?categorie=${categorieId}` : '/api/vetements/';
  const r = await fetch(url, { ...defaults });
  if (!r.ok) throw new Error('Erreur chargement vêtements');
  const data = await r.json();
  return data.vetements ?? [];
}

export async function authStatus(): Promise<boolean> {
  const r = await fetch('/api/auth/status/', { ...defaults });
  if (!r.ok) return false;
  const data = await r.json();
  return data.authenticated === true;
}

export async function uploadImages(formData: FormData): Promise<void> {
  const csrf = getCsrfToken();
  const r = await fetch('/upload/', {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf },
    body: formData,
  });
  if (!r.ok) throw new Error('Erreur upload');
  const data = await r.json().catch(() => ({}));
  if (data && data.success !== true && r.status === 200) throw new Error('Upload échoué');
}

export async function updateVetementName(id: number, nom: string): Promise<void> {
  const r = await fetch(`/update_vetement_name/${id}/`, {
    method: 'POST',
    ...defaults,
    headers: {
      ...defaults.headers as Record<string, string>,
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({ nom }),
  });
  if (!r.ok) throw new Error('Erreur mise à jour');
  const data = await r.json();
  if (!data.success) throw new Error(data.message || 'Erreur');
}

export async function deleteVetement(id: number): Promise<void> {
  const r = await fetch(`/delete_vetement_image/${id}/`, {
    method: 'DELETE',
    ...defaults,
    headers: { ...defaults.headers as Record<string, string>, 'X-CSRFToken': getCsrfToken() },
  });
  if (!r.ok) throw new Error('Erreur suppression');
}
