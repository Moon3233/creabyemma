/**
 * URL de base WebSocket.
 * En dev avec proxy Vite, même origine (5173) puis proxy vers 8000.
 */
export function getWebSocketBaseUrl(apiBaseUrl?: string): string {
  if (typeof window === 'undefined') return 'ws://localhost:8000';
  if (apiBaseUrl) {
    try {
      const url = new URL(apiBaseUrl.replace(/\/$/, ''));
      if (url.protocol === 'ws:' || url.protocol === 'wss:') return `${url.protocol}//${url.host}`;
      const wsScheme = url.protocol === 'https:' ? 'wss' : 'ws';
      return `${wsScheme}://${url.host}`;
    } catch {
      return 'ws://localhost:8000';
    }
  }
  const host = window.location.hostname;
  const port = window.location.port;
  if ((host === 'localhost' || host === '127.0.0.1') && (port === '5173' || port === '5174')) {
    return `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${host}:${port}`;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}`;
}
