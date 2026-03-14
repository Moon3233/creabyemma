/**
 * Store et utilitaires pour le chat visiteur (sans connexion).
 * Token guest dans localStorage.
 */
const CHAT_TOKEN_KEY = 'creabyemma_chat_token';
const CHAT_LAST_SEEN_KEY = 'creabyemma_chat_last_seen';

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getOrCreateGuestToken(): string {
  if (typeof window === 'undefined') return '';
  let token = localStorage.getItem(CHAT_TOKEN_KEY);
  if (!token) {
    token = generateUUID();
    localStorage.setItem(CHAT_TOKEN_KEY, token);
  }
  return token;
}

export function initGuestToken(): string {
  return getOrCreateGuestToken();
}

export function getLastSeenMessageId(): number {
  if (typeof window === 'undefined') return 0;
  const v = localStorage.getItem(CHAT_LAST_SEEN_KEY);
  return v ? parseInt(v, 10) || 0 : 0;
}

export function setLastSeenMessageId(id: number): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(CHAT_LAST_SEEN_KEY, String(id));
}
