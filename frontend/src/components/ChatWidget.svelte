<script lang="ts">
  import { tick } from 'svelte';
  import { slide } from 'svelte/transition';
  import { initGuestToken, getLastSeenMessageId, setLastSeenMessageId } from '../lib/chatStore';
  import { chatGet, chatPost } from '../lib/chatApi';
  import { getWebSocketBaseUrl } from '../lib/wsUtils';
  import { chatOpenStore } from '../lib/chatOpenStore';

  const WS_BASE = getWebSocketBaseUrl();

  interface Message {
    id: number;
    sender_type: 'guest' | 'admin';
    content: string;
    created_at: string;
  }

  interface Conversation {
    id: number | null;
    guest_token: string;
    guest_email: string | null;
    guest_phone: string | null;
    guest_first_name: string | null;
    guest_last_name: string | null;
  }

  let open = $state(false);
  let token = $state('');
  let messages = $state<Message[]>([]);
  let loading = $state(false);
  let error = $state<string | null>(null);
  let inputText = $state('');
  let sending = $state(false);
  let ws: WebSocket | null = null;
  let wsConnected = $state(false);
  let reconnectAttempts = 0;
  const MAX_RECONNECT = 5;
  let showGuestInfoForm = $state(false);
  let guestInfoSubmitted = $state(false);
  let guestInfo = $state({ email: '', phone: '', first_name: '', last_name: '' });
  let messagesContainerEl = $state<HTMLDivElement | null>(null);
  let unreadCount = $state(0);

  function scrollToBottom(force = false) {
    const el = messagesContainerEl;
    if (!el) return;
    const threshold = 80;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    if (!force && !isNearBottom) return;
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
      });
    });
  }

  function formatTime(iso: string): string {
    try {
      return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  }

  async function loadConversation(): Promise<void> {
    if (!token) return;
    loading = true;
    error = null;
    try {
      const data = await chatGet<{ conversation: Conversation; messages: Message[]; is_new: boolean }>(
        `/api/chat/conversation/?token=${token}`
      );
      messages = data.messages || [];
      await tick();
      scrollToBottom(true);
      const hasGuestMsg = messages.some((m) => m.sender_type === 'guest');
      const conv = data.conversation;
      const hasNoInfo = !conv?.guest_email && !conv?.guest_phone && !conv?.guest_first_name && !conv?.guest_last_name;
      if (hasGuestMsg && hasNoInfo) showGuestInfoForm = true;
      const maxId = Math.max(0, ...messages.map((m) => m.id).filter((id) => id > 0));
      if (maxId > 0) setLastSeenMessageId(maxId);
      unreadCount = 0;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Erreur de chargement';
    } finally {
      loading = false;
    }
  }

  function connectWs(): void {
    if (!token || ws?.readyState === WebSocket.OPEN) return;
    const url = `${WS_BASE}/ws/chat/${token}/`;
    ws = new WebSocket(url);
    ws.onopen = () => {
      reconnectAttempts = 0;
      wsConnected = true;
    };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === 'new_message' || data.type === 'message_sent') {
          const msg = data.message;
          if (!msg) return;
          if (open) {
            const hasOptimistic = messages.some((m) => m.id < 0 && m.content === msg.content);
            if (hasOptimistic) {
              messages = messages.map((m) => (m.id < 0 && m.content === msg.content ? msg : m));
            } else {
              messages = [...messages, msg];
            }
            if (msg?.sender_type === 'guest' && messages.filter((m) => m.sender_type === 'guest').length === 1) {
              showGuestInfoForm = true;
            }
            tick().then(() => scrollToBottom(false));
          }
          if (msg?.sender_type === 'admin' && msg?.id) {
            setLastSeenMessageId(Math.max(getLastSeenMessageId(), msg.id));
            if (open) unreadCount = 0;
            else unreadCount += 1;
          }
        } else if (data.type === 'error') {
          error = data.message || 'Erreur';
        }
      } catch {
        //
      }
    };
    ws.onclose = () => {
      ws = null;
      wsConnected = false;
      if (reconnectAttempts < MAX_RECONNECT) {
        reconnectAttempts++;
        setTimeout(connectWs, 2000);
      }
    };
    ws.onerror = () => {};
  }

  function sendMessage(): void {
    const content = inputText.trim();
    if (!content || sending || !wsConnected || !ws || ws.readyState !== WebSocket.OPEN) return;
    sending = true;
    const optimisticMsg: Message = {
      id: -Date.now(),
      sender_type: 'guest',
      content,
      created_at: new Date().toISOString(),
    };
    messages = [...messages, optimisticMsg];
    inputText = '';
    ws.send(JSON.stringify({ type: 'guest_message', content }));
    sending = false;
    tick().then(() => scrollToBottom(true));
  }

  async function submitGuestInfo(): Promise<void> {
    try {
      await chatPost('/api/chat/guest-info/', { token, ...guestInfo });
      guestInfoSubmitted = true;
      showGuestInfoForm = false;
    } catch {
      error = "Erreur lors de l'enregistrement";
    }
  }

  function skipGuestInfo(): void {
    guestInfoSubmitted = true;
    showGuestInfoForm = false;
  }

  function toggle(): void {
    open = !open;
    if (open && token) {
      connectWs();
      loadConversation();
      unreadCount = 0;
    }
  }

  async function checkUnread(): Promise<void> {
    if (!token) return;
    try {
      const data = await chatGet<{ messages: Message[] }>(`/api/chat/conversation/?token=${token}`);
      const adminMsgs = (data.messages || []).filter((m) => m.sender_type === 'admin');
      const lastSeen = getLastSeenMessageId();
      unreadCount = adminMsgs.filter((m) => m.id > lastSeen).length;
    } catch {
      //
    }
  }

  $effect(() => {
    const shouldOpen = $chatOpenStore;
    if (shouldOpen && !open) {
      open = true;
      if (token) {
        connectWs();
        loadConversation();
      }
      chatOpenStore.set(false);
    }
  });

  $effect(() => {
    if (typeof document === 'undefined') return;
    token = initGuestToken();
    if (token) {
      if (open) {
        connectWs();
        loadConversation();
      }
      checkUnread();
      const iv = setInterval(checkUnread, 60000);
      return () => clearInterval(iv);
    }
  });
</script>

<button
  class="chat-trigger"
  type="button"
  class:chat-trigger--unread={unreadCount > 0}
  aria-label={unreadCount > 0 ? `Ouvrir le chat — ${unreadCount} message${unreadCount > 1 ? 's' : ''} non lu${unreadCount > 1 ? 's' : ''}` : 'Ouvrir le chat'}
  onclick={toggle}
  aria-expanded={open}
>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="chat-trigger-icon">
    <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
  {#if unreadCount > 0}
    <span class="chat-trigger-badge" aria-hidden="true">{unreadCount > 99 ? '99+' : unreadCount}</span>
  {/if}
</button>

{#if open}
  <div class="chat-panel" transition:slide={{ duration: 200 }}>
    <div class="chat-header">
      <h3>Contact</h3>
      <button type="button" class="chat-close" aria-label="Fermer" onclick={toggle}>×</button>
    </div>

    {#if loading}
      <div class="chat-loading">Chargement…</div>
    {:else if error}
      <div class="chat-error">{error}</div>
    {:else}
      <div class="chat-messages" bind:this={messagesContainerEl}>
        {#if messages.length === 0}
          <p class="chat-intro">
            Bienvenue ! Posez-moi vos questions — je vous répondrai dès que possible.
          </p>
        {/if}
        {#each messages as msg (msg.id)}
          <div class="chat-msg chat-msg-{msg.sender_type}">
            <span class="chat-msg-content">{msg.content}</span>
            <span class="chat-msg-time">{formatTime(msg.created_at)}</span>
          </div>
        {/each}
        {#if messages.some((m) => m.sender_type === 'guest') && !messages.some((m) => m.sender_type === 'admin')}
          <p class="chat-awaiting-reply">Merci pour votre message. Je vous répondrai dès que possible.</p>
        {/if}
      </div>

      {#if showGuestInfoForm && !guestInfoSubmitted}
        <div class="chat-guest-info">
          <p class="chat-guest-info-title">Vos coordonnées pour que je puisse vous recontacter ?</p>
          <form onsubmit={(e) => { e.preventDefault(); submitGuestInfo(); }}>
            <input type="text" bind:value={guestInfo.first_name} placeholder="Prénom" />
            <input type="text" bind:value={guestInfo.last_name} placeholder="Nom" />
            <input type="email" bind:value={guestInfo.email} placeholder="Email" />
            <input type="tel" bind:value={guestInfo.phone} placeholder="Téléphone" />
            <div class="chat-guest-info-actions">
              <button type="submit">Enregistrer</button>
              <button type="button" onclick={skipGuestInfo}>Passer</button>
            </div>
          </form>
        </div>
      {:else}
        {#if !wsConnected}
          <p class="chat-ws-status"><span class="chat-ws-status-dot"></span> Connexion en cours…</p>
        {/if}
        <form class="chat-form" onsubmit={(e) => { e.preventDefault(); sendMessage(); }}>
          <input
            type="text"
            bind:value={inputText}
            placeholder="Votre message…"
            maxlength="2000"
            disabled={!wsConnected}
          />
          <button type="submit" disabled={!inputText.trim() || sending || !wsConnected}>Envoyer</button>
        </form>
      {/if}
    {/if}
  </div>
{/if}

<style>
  .chat-trigger {
    position: fixed;
    bottom: max(1.25rem, env(safe-area-inset-bottom));
    right: max(1.25rem, env(safe-area-inset-right));
    width: 4.25rem;
    height: 4.25rem;
    border-radius: 50%;
    background: linear-gradient(145deg, #c49dbe 0%, #bb90b4 100%);
    color: white;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(187, 144, 180, 0.45), 0 2px 8px rgba(0, 0, 0, 0.08);
    transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
    z-index: 9998;
  }
  .chat-trigger:hover {
    background: linear-gradient(145deg, #d46a7d 0%, #cd5f72 100%);
    transform: scale(1.05);
    box-shadow: 0 6px 24px rgba(205, 95, 114, 0.4), 0 2px 12px rgba(0, 0, 0, 0.1);
  }
  .chat-trigger:active {
    transform: scale(0.98);
  }
  .chat-trigger--unread {
    animation: chatTriggerPulse 2.5s ease-in-out infinite;
  }
  @keyframes chatTriggerPulse {
    0%, 100% { box-shadow: 0 4px 16px rgba(187, 144, 180, 0.4); }
    50% { box-shadow: 0 4px 24px rgba(205, 95, 114, 0.5), 0 0 0 3px rgba(205, 95, 114, 0.2); }
  }
  .chat-trigger-badge {
    position: absolute;
    top: -0.2rem;
    right: -0.2rem;
    min-width: 1.5rem;
    height: 1.5rem;
    padding: 0 0.4rem;
    background: #cd5f72;
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 0 2.5px white;
  }
  .chat-trigger-icon {
    width: 2.25rem;
    height: 2.25rem;
    flex-shrink: 0;
  }

  .chat-panel {
    --chat-bg: #fff;
    --chat-surface: #f5f0f4;
    --chat-border: rgba(187, 144, 180, 0.25);
    --chat-accent: #bb90b4;
    position: fixed;
    bottom: max(5rem, env(safe-area-inset-bottom) + 4rem);
    right: max(1rem, env(safe-area-inset-right));
    width: min(28rem, calc(100vw - 2rem));
    min-height: 28rem;
    max-height: min(38rem, 85dvh);
    background: var(--chat-bg);
    border-radius: 1rem;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12), 0 0 0 1px var(--chat-border);
    display: flex;
    flex-direction: column;
    z-index: 9999;
    overflow: hidden;
    font-family: 'Playwrite GB S', cursive;
  }

  .chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    background: var(--chat-surface);
    border-bottom: 1px solid var(--chat-border);
    color: #cd5f72;
    flex-shrink: 0;
  }
  .chat-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
  }
  .chat-close {
    background: transparent;
    border: 1px solid var(--chat-border);
    color: #bb90b4;
    font-size: 1.25rem;
    cursor: pointer;
    width: 2rem;
    height: 2rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
  }
  .chat-close:hover {
    background: rgba(187, 144, 180, 0.15);
  }

  .chat-loading,
  .chat-error {
    padding: 1.5rem;
    text-align: center;
    color: #cd5f72;
    font-size: 0.9rem;
  }
  .chat-error {
    color: #c00;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    min-height: 8rem;
  }

  .chat-intro {
    margin: 0;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    line-height: 1.5;
    color: #666;
    background: var(--chat-surface);
    border-radius: 0.75rem;
    border: 1px solid var(--chat-border);
    align-self: flex-start;
    max-width: 90%;
  }

  .chat-awaiting-reply {
    margin: 0;
    padding: 0.5rem 0;
    font-size: 0.8rem;
    color: #666;
    font-style: italic;
  }

  .chat-msg {
    max-width: 82%;
    padding: 0.6rem 0.9rem;
    border-radius: 1rem;
    align-self: flex-start;
  }
  .chat-msg-admin {
    align-self: flex-end;
    background: #e8e0e6;
    color: #333;
    border-bottom-right-radius: 0.25rem;
  }
  .chat-msg-guest {
    background: var(--chat-surface);
    color: #333;
    border: 1px solid var(--chat-border);
    border-bottom-left-radius: 0.25rem;
  }
  .chat-msg-content {
    display: block;
    word-break: break-word;
    font-size: 0.9rem;
    line-height: 1.45;
  }
  .chat-msg-time {
    font-size: 0.7rem;
    color: #666;
    margin-top: 0.25rem;
  }

  .chat-guest-info {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--chat-border);
    flex-shrink: 0;
  }
  .chat-guest-info-title {
    font-size: 0.8rem;
    color: #666;
    margin: 0 0 0.5rem 0;
  }
  .chat-guest-info form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.35rem 0.5rem;
  }
  .chat-guest-info input {
    width: 100%;
    box-sizing: border-box;
    padding: 0.4rem 0.6rem;
    border-radius: 0.5rem;
    border: 1px solid var(--chat-border);
    font-size: 0.8rem;
    font-family: inherit;
  }
  .chat-guest-info-actions {
    display: flex;
    gap: 0.35rem;
    margin-top: 0.5rem;
    grid-column: 1 / -1;
  }
  .chat-guest-info-actions button {
    flex: 1;
    padding: 0.4rem 0.6rem;
    border-radius: 0.5rem;
    border: none;
    cursor: pointer;
    font-size: 0.8rem;
    font-family: inherit;
  }
  .chat-guest-info-actions button[type="submit"] {
    background: var(--chat-accent);
    color: white;
  }
  .chat-guest-info-actions button[type="button"] {
    background: transparent;
    border: 1px solid var(--chat-border);
    color: #666;
  }

  .chat-ws-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    margin: 0;
    font-size: 0.8rem;
    color: #666;
  }
  .chat-ws-status-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background: var(--chat-accent);
    animation: chatPulse 1.2s ease-in-out infinite;
  }
  @keyframes chatPulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
  }

  .chat-form {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    padding-bottom: max(0.75rem, env(safe-area-inset-bottom));
    border-top: 1px solid var(--chat-border);
    flex-shrink: 0;
  }
  .chat-form input {
    flex: 1;
    min-width: 0;
    padding: 0.5rem 0.75rem;
    border-radius: 0.75rem;
    border: 1px solid var(--chat-border);
    font-size: 0.9rem;
    font-family: inherit;
  }
  .chat-form button {
    padding: 0.5rem 1rem;
    border-radius: 0.75rem;
    border: none;
    background: var(--chat-accent);
    color: white;
    cursor: pointer;
    font-size: 0.9rem;
    font-family: inherit;
    flex-shrink: 0;
  }
  .chat-form button:hover:not(:disabled) {
    background: #cd5f72;
  }
  .chat-form button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
