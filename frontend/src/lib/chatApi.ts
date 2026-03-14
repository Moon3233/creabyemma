/**
 * API chat : fetch avec credentials (cookies session pour admin).
 */
import { ensureCsrf } from './csrf';

export async function chatFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(endpoint, {
    ...options,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(options.headers as Record<string, string>),
    },
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { error?: string };
    throw new Error(err.error || `Erreur ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function chatGet<T>(endpoint: string): Promise<T> {
  return chatFetch<T>(endpoint, { method: 'GET' });
}

export async function chatPost<T>(endpoint: string, body: unknown): Promise<T> {
  const token = await ensureCsrf();
  return chatFetch<T>(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
    body: JSON.stringify(body),
  });
}

export async function chatDelete<T>(endpoint: string): Promise<T> {
  const token = await ensureCsrf();
  return chatFetch<T>(endpoint, {
    method: 'DELETE',
    headers: { 'X-CSRFToken': token },
  });
}
