/**
 * Récupère le cookie CSRF Django pour les requêtes POST.
 * GET sans cache pour forcer Set-Cookie ; secours GET /login/ (page Django complète).
 */
function readCsrfCookie(): string {
  const name = 'csrftoken';
  for (const c of document.cookie.split(';')) {
    const [key, value] = c.trim().split('=');
    if (key === name && value) return decodeURIComponent(value);
  }
  return '';
}

export async function ensureCsrf(): Promise<string> {
  let token = readCsrfCookie();
  if (token) return token;

  const opts: RequestInit = { credentials: 'include', cache: 'no-store' };
  await fetch('/api/auth/status/', opts);
  token = readCsrfCookie();
  if (token) return token;

  await fetch('/login/', opts);
  token = readCsrfCookie();
  return token;
}
