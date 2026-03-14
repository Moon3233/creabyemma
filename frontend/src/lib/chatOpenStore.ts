/**
 * Store pour ouvrir/fermer le chat depuis n'importe quelle page (ex: Contact).
 */
import { writable } from 'svelte/store';

export const chatOpenStore = writable(false);

export function openChat() {
  chatOpenStore.set(true);
}
