<script lang="ts">
  import { push } from 'svelte-spa-router';
  import { ensureCsrf } from '../lib/csrf';
  import { auth } from '../stores/auth';
  import { setPageMeta } from '../lib/pageMeta';

  let username = $state('');
  let password = $state('');
  let loading = $state(false);
  let error = $state('');
  let showPassword = $state(false);

  async function onSubmit(e: Event) {
    e.preventDefault();
    if (!username.trim() || !password) return;
    loading = true;
    error = '';
    try {
      const csrf = await ensureCsrf();
      const form = new FormData();
      form.append('username', username.trim());
      form.append('password', password);
      form.append('csrfmiddlewaretoken', csrf);
      form.append('next', typeof window !== 'undefined' ? window.location.origin + '/' : '/');

      const r = await fetch('/login/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf },
        body: form,
        redirect: 'manual',
      });

      // Succès : 302 (redirect Django) ou opaqueredirect (fetch ne suit pas la redirection)
      const isRedirect = r.status === 302 || r.type === 'opaqueredirect';
      if (r.ok || isRedirect) {
        await auth.refresh();
        push('/');
        return;
      }
      error = 'Identifiants incorrects.';
    } catch (_) {
      error = 'Erreur de connexion.';
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    setPageMeta({ title: 'Connexion', description: 'Connexion à l\'espace administration Creabyemma' });
  });
</script>

<main class="login-main">
  <h1>Se connecter</h1>
  <form onsubmit={onSubmit}>
    <div>
      <label for="username">Nom d'utilisateur</label>
      <input
        type="text"
        id="username"
        name="username"
        bind:value={username}
        required
        autocomplete="username"
        spellcheck="false"
      />
    </div>
    <div class="password-field">
      <label for="password">Mot de passe</label>
      <div class="password-input-row">
        <input
          type={showPassword ? 'text' : 'password'}
          id="password"
          name="password"
          bind:value={password}
          required
          autocomplete="current-password"
          class="password-input"
        />
        <button
          type="button"
          class="password-toggle"
          aria-pressed={showPassword}
          aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
          onclick={() => (showPassword = !showPassword)}
        >
          {#if showPassword}
            <svg class="password-toggle-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          {:else}
            <svg class="password-toggle-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          {/if}
        </button>
      </div>
    </div>
    {#if error}<p class="error">{error}</p>{/if}
    <button type="submit" disabled={loading}>{loading ? 'Connexion…' : 'Connexion'}</button>
  </form>
</main>

<style>
  .login-main {
    max-width: 20rem;
    margin: 0 auto;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .login-main form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .login-main label {
    display: block;
    margin-bottom: 0.25rem;
    color: #cd5f72;
    font-family: 'Playwrite GB S', cursive;
  }
  .login-main input:not(.password-input) {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    border: 1px solid #bb90b4;
  }
  .password-field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .password-input-row {
    display: flex;
    align-items: stretch;
    gap: 0;
    border-radius: 0.5rem;
    border: 1px solid #bb90b4;
    overflow: hidden;
    background: #fff;
  }
  .password-input {
    flex: 1;
    min-width: 0;
    padding: 0.5rem 0.75rem;
    border: none;
    border-radius: 0;
    outline: none;
    font: inherit;
  }
  .password-input:focus-visible {
    box-shadow: inset 0 0 0 2px rgba(187, 144, 180, 0.45);
  }
  .password-toggle {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.75rem;
    padding: 0;
    border: none;
    border-left: 1px solid rgba(187, 144, 180, 0.35);
    background: rgba(245, 240, 244, 0.6);
    color: #8a6b85;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease;
  }
  .password-toggle:hover {
    background: rgba(187, 144, 180, 0.2);
    color: #cd5f72;
  }
  .password-toggle:focus-visible {
    outline: 2px solid #bb90b4;
    outline-offset: 2px;
  }
  .password-toggle-icon {
    width: 1.25rem;
    height: 1.25rem;
  }
  .login-main button[type='submit'] {
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    border: 2px solid #bb90b4;
    background: white;
    color: #bb90b4;
    font-family: 'Playwrite GB S', cursive;
    cursor: pointer;
  }
  .login-main button[type='submit']:disabled {
    opacity: 0.7;
  }
  .error {
    color: #c00;
    font-size: 0.9rem;
  }
</style>
