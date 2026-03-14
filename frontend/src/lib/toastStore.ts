/**
 * Store de notifications toast (sans alert/confirm).
 */
import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

const DURATION = 4000;
let nextId = 0;

function createToastStore() {
  const { subscribe, set, update } = writable<Toast[]>([]);

  return {
    subscribe,
    add(message: string, type: ToastType = 'info') {
      const id = ++nextId;
      const toast: Toast = { id, message, type };
      update((list) => [...list, toast]);
      setTimeout(() => {
        update((list) => list.filter((t) => t.id !== id));
      }, DURATION);
      return id;
    },
    remove(id: number) {
      update((list) => list.filter((t) => t.id !== id));
    },
  };
}

export const toastStore = createToastStore();

export function showToast(message: string, type: ToastType = 'info'): number {
  return toastStore.add(message, type);
}
