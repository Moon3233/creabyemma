<script lang="ts">
  import { slide } from 'svelte/transition';
  import { toastStore } from '../lib/toastStore';
  import type { Toast } from '../lib/toastStore';
</script>

<div class="toast-container" role="region" aria-label="Notifications">
  {#each $toastStore as toast (toast.id)}
    <div
      class="toast toast--{toast.type}"
      transition:slide={{ duration: 200 }}
      role="status"
      aria-live="polite"
    >
      <span class="toast-message">{toast.message}</span>
      <button
        type="button"
        class="toast-close"
        aria-label="Fermer"
        onclick={() => toastStore.remove(toast.id)}
      >
        ×
      </button>
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    bottom: max(5rem, env(safe-area-inset-bottom) + 4rem);
    left: 50%;
    transform: translateX(-50%);
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: min(90vw, 24rem);
    pointer-events: none;
  }
  .toast-container > * {
    pointer-events: auto;
  }
  .toast {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: 0.75rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    font-family: 'Playwrite GB S', cursive;
    font-size: 0.9rem;
  }
  .toast--success {
    background: #2c9932;
    color: white;
  }
  .toast--error {
    background: #c00;
    color: white;
  }
  .toast--info {
    background: #bb90b4;
    color: white;
  }
  .toast-message {
    flex: 1;
  }
  .toast-close {
    background: transparent;
    border: none;
    color: inherit;
    font-size: 1.25rem;
    cursor: pointer;
    opacity: 0.8;
    line-height: 1;
    padding: 0 0.25rem;
  }
  .toast-close:hover {
    opacity: 1;
  }
</style>
