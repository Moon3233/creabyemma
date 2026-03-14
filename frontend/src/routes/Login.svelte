<script lang="ts">
  import { push } from 'svelte-spa-router';
  import { ensureCsrf } from '../lib/csrf';
  import { auth } from '../stores/auth';
  import { setPageMeta } from '../lib/pageMeta';

  let username = $state('');
  let password = $state('');
  let loading = $state(false);
  let error = $state('');

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
    <div>
      <label for="password">Mot de passe</label>
      <input
        type="password"
        id="password"
        name="password"
        bind:value={password}
        required
        autocomplete="current-password"
      />
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
  .login-main input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    border: 1px solid #bb90b4;
  }
  .login-main button {
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    border: 2px solid #bb90b4;
    background: white;
    color: #bb90b4;
    font-family: 'Playwrite GB S', cursive;
    cursor: pointer;
  }
  .login-main button:disabled {
    opacity: 0.7;
  }
  .error {
    color: #c00;
    font-size: 0.9rem;
  }
</style>
