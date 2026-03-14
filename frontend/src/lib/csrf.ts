/**
 * Récupère le cookie CSRF Django pour les requêtes POST.
 * On fait d'abord une requête GET vers l'origine Django pour obtenir le cookie.
 */
export async function ensureCsrf(): Promise<string> {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (const c of cookies) {
    const [key, value] = c.trim().split('=');
    if (key === name && value) return decodeURIComponent(value);
  }
  await fetch('/api/auth/status/', { credentials: 'include' });
  for (const c of document.cookie.split(';')) {
    const [key, value] = c.trim().split('=');
    if (key === name && value) return decodeURIComponent(value);
  }
  return '';
}
