/**
 * Store du nombre de messages non lus côté admin.
 * Utilisé pour afficher le badge sur le lien "Gestion" dans la navbar.
 * Mis à jour via WebSocket (pas de polling).
 */
import { writable } from 'svelte/store';
import { chatGet } from '../lib/chatApi';

function createAdminUnreadStore() {
  const { subscribe, set } = writable<number>(0);

  async function refresh(): Promise<number> {
    try {
      const data = await chatGet<{ unread_count: number }>('/api/chat/admin/unread-count/');
      const count = data.unread_count ?? 0;
      set(count);
      return count;
    } catch {
      set(0);
      return 0;
    }
  }

  function reset(): void {
    set(0);
  }

  return {
    subscribe,
    refresh,
    reset,
  };
}

export const adminUnreadStore = createAdminUnreadStore();
