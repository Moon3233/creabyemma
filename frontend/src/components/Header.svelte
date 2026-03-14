<script lang="ts">
  import { push } from 'svelte-spa-router';
  import { auth } from '../stores/auth';
  import { adminUnreadStore } from '../stores/adminUnreadStore';

  let menuOpen = $state(false);

  function toggleMenu() {
    menuOpen = !menuOpen;
  }

  function closeMenu(e: MouseEvent) {
    const t = e.target as Node;
    if (menuOpen && !document.querySelector('.burger-menu')?.contains(t) && !document.querySelector('.header-nav')?.contains(t)) {
      menuOpen = false;
    }
  }

</script>

<svelte:window onclick={closeMenu} />

<header>
  <div class="logo-container-header">
    <a href="/" onclick={(e) => { e.preventDefault(); push('/'); }}>
      <img src="/static/images/creabyemmalogo.png" alt="Logo Creabyemma" class="logo-header" />
    </a>
  </div>
  <nav class="header-nav" class:active={menuOpen}>
    <ul>
      <li><a href="/" onclick={(e) => { e.preventDefault(); push('/'); menuOpen = false; }}>Printemps 🌸 & Été ☀️</a></li>
      <li><a href="/contact" onclick={(e) => { e.preventDefault(); push('/contact'); menuOpen = false; }}>Contact</a></li>
      {#if $auth}
        <li class="gestion-link">
          <a href="/gestion" onclick={(e) => { e.preventDefault(); push('/gestion'); menuOpen = false; }} aria-label={$adminUnreadStore > 0 ? `Gestion — ${$adminUnreadStore} message${$adminUnreadStore > 1 ? 's' : ''} non lu${$adminUnreadStore > 1 ? 's' : ''}` : 'Gestion'}>
            Gestion
            {#if $adminUnreadStore > 0}
              <span class="gestion-badge" aria-hidden="true">{$adminUnreadStore > 99 ? '99+' : $adminUnreadStore}</span>
            {/if}
          </a>
        </li>
        <li><a href="/logout" onclick={(e) => { e.preventDefault(); window.location.href = '/logout'; }}>Déconnexion</a></li>
      {:else}
        <li><a href="/login" onclick={(e) => { e.preventDefault(); push('/login'); menuOpen = false; }}>Connexion</a></li>
      {/if}
    </ul>
  </nav>
  <button type="button" class="burger-menu" aria-label="Menu" onclick={toggleMenu}>
    <span></span>
    <span></span>
    <span></span>
  </button>
</header>
