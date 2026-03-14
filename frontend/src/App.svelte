<script lang="ts">
  import Router from 'svelte-spa-router';
  import { wrap } from 'svelte-spa-router/wrap';
  import Header from './components/Header.svelte';
  import Footer from './components/Footer.svelte';
  import ChatWidget from './components/ChatWidget.svelte';
  import Toast from './components/Toast.svelte';
  import { auth } from './stores/auth';
  import { adminUnreadStore } from './stores/adminUnreadStore';
  import { getWebSocketBaseUrl } from './lib/wsUtils';

  const routes = {
    '/': wrap({ asyncComponent: () => import('./routes/Home.svelte') }),
    '/contact': wrap({ asyncComponent: () => import('./routes/Contact.svelte') }),
    '/login': wrap({ asyncComponent: () => import('./routes/Login.svelte') }),
    '/gestion': wrap({ asyncComponent: () => import('./routes/Gestion.svelte') }),
  };

  $effect(() => {
    auth.refresh();
  });

  // WebSocket admin pour le badge "messages non lus" (temps réel, pas de polling)
  $effect(() => {
    if (!$auth) {
      adminUnreadStore.reset();
      return;
    }
    const wsBase = getWebSocketBaseUrl();
    const ws = new WebSocket(`${wsBase}/ws/chat/admin/`);
    ws.onopen = () => adminUnreadStore.refresh();
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        const msg = data.message;
        if ((data.type === 'new_message' || data.type === 'message_sent') && msg?.sender_type === 'guest') {
          adminUnreadStore.refresh();
        }
      } catch {
        //
      }
    };
    return () => ws.close();
  });
</script>

<div class="app">
  <Header />
  <div class="page">
    <div class="page-wrapper">
      <Router {routes} />
    </div>
  </div>
  <Footer />
  <ChatWidget />
  <Toast />
</div>

<style>
  .app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }
  .page {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: stretch;
    width: 100%;
    min-width: 0;
    justify-content: flex-start;
    padding-top: clamp(1.5rem, 4vw, 2.5rem);
    padding-bottom: clamp(1.5rem, 4vw, 2.5rem);
  }
  .page-wrapper {
    width: 100%;
    min-width: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
  }
</style>
