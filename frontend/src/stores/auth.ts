import { writable } from 'svelte/store';
import { authStatus } from '../lib/api';

function createAuthStore() {
  const { subscribe, set } = writable<boolean>(false);

  return {
    subscribe,
    set,
    async refresh() {
      const ok = await authStatus();
      set(ok);
      return ok;
    },
  };
}

export const auth = createAuthStore();
