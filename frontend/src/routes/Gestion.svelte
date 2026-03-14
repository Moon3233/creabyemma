<script lang="ts">
  import { push } from 'svelte-spa-router';
  import { tick } from 'svelte';
  import { chatGet, chatPost, chatDelete } from '../lib/chatApi';
  import { getWebSocketBaseUrl } from '../lib/wsUtils';
  import { setPageMeta } from '../lib/pageMeta';
  import { adminUnreadStore } from '../stores/adminUnreadStore';

  const WS_BASE = getWebSocketBaseUrl();

  interface Conversation {
    id: number;
    guest_token: string;
    guest_email: string | null;
    guest_phone: string | null;
    guest_first_name: string | null;
    guest_last_name: string | null;
    is_blocked?: boolean;
    created_at: string;
    updated_at: string;
    last_message: { content: string; created_at: string; sender_type: string } | null;
    unread_count: number;
  }

  interface Message {
    id: number;
    sender_type: 'guest' | 'admin';
    content: string;
    created_at: string;
    is_read_by_admin?: boolean;
  }

  let conversations = $state<Conversation[]>([]);
  let selectedConv = $state<Conversation | null>(null);
  let messages = $state<Message[]>([]);
  let loading = $state(true);
  let loadingMessages = $state(false);
  let replyText = $state('');
  let sending = $state(false);
  let ws = $state<WebSocket | null>(null);
  let wsOpen = $state(false);
  let error = $state('');
  let confirmDelete = $state<Conversation | null>(null);
  let messagesContainerEl = $state<HTMLDivElement | null>(null);
  let actionLoading = $state(false);

  function guestLabel(c: Conversation): string {
    const parts = [c.guest_first_name, c.guest_last_name].filter(Boolean);
    if (parts.length) return parts.join(' ');
    if (c.guest_email) return c.guest_email;
    if (c.guest_phone) return c.guest_phone;
    return `${String(c.guest_token).slice(0, 8)}…`;
  }

  function formatTime(iso: string): string {
    try {
      return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  }

  function formatDate(iso: string): string {
    try {
      return new Date(iso).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '';
    }
  }

  function scrollToBottom(force = false) {
    const el = messagesContainerEl;
    if (!el) return;
    const threshold = 80;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    if (!force && !isNearBottom) return;
    requestAnimationFrame(() => {
      requestAnimationFrame(() => el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' }));
    });
  }

  async function loadConversations() {
    loading = true;
    error = '';
    try {
      const data = await chatGet<{ conversations: Conversation[] }>('/api/chat/admin/conversations/');
      conversations = data.conversations || [];
      if (conversations.length > 0 && !selectedConv) {
        loadMessages(conversations[0]);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Erreur';
      if (msg.includes('401') || msg.includes('403') || msg.includes('Non authentifié') || msg.includes('Accès réservé')) {
        push('/login');
        return;
      }
      error = msg;
    } finally {
      loading = false;
    }
  }

  async function loadMessages(conv: Conversation) {
    selectedConv = conv;
    confirmDelete = null;
    loadingMessages = true;
    replyText = '';
    try {
      const data = await chatGet<{ messages: Message[] }>(
        `/api/chat/admin/conversations/${conv.id}/messages/`
      );
      messages = data.messages || [];
      await chatPost(`/api/chat/admin/conversations/${conv.id}/mark-read/`, {});
      conv.unread_count = 0;
      adminUnreadStore.refresh();
    } catch (e) {
      messages = [];
      error = e instanceof Error ? e.message : 'Erreur';
    } finally {
      loadingMessages = false;
      tick().then(() => scrollToBottom(true));
    }
    connectAdminWs();
  }

  function connectAdminWs() {
    if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) return;
    ws?.close();
    ws = null;
    wsOpen = false;
    const url = `${WS_BASE}/ws/chat/admin/`;
    const socket = new WebSocket(url);
    ws = socket;
    socket.onopen = () => {
      wsOpen = true;
    };
    socket.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        const convId = data.conversation_id ?? data.message?.conversation_id;
        const msg = data.message as Message | undefined;

        if ((data.type === 'new_message' || data.type === 'message_sent') && msg && convId) {
          if (msg.sender_type === 'guest') adminUnreadStore.refresh();
          if (convId === selectedConv?.id) {
            const hasOptimistic = messages.some((m) => m.id < 0 && m.content === msg.content);
            if (hasOptimistic) {
              messages = messages.map((m) => (m.id < 0 && m.content === msg.content ? msg : m));
            } else {
              messages = [...messages, msg];
            }
          }
          const existing = conversations.find((c) => c.id === convId);
          if (existing) {
            conversations = conversations.map((c) =>
              c.id === convId
                ? {
                    ...c,
                    last_message: {
                      content: (msg.content || '').slice(0, 100),
                      created_at: msg.created_at,
                      sender_type: msg.sender_type,
                    },
                    updated_at: msg.created_at,
                    unread_count:
                      msg.sender_type === 'guest' && convId !== selectedConv?.id
                        ? (existing.unread_count || 0) + 1
                        : existing.unread_count,
                  }
                : c
            );
          } else {
            loadConversations();
          }
        }
      } catch {
        //
      }
    };
    socket.onclose = () => {
      ws = null;
      wsOpen = false;
    };
    socket.onerror = () => {};
  }

  function sendReply() {
    const content = replyText.trim();
    if (!content || !selectedConv || sending || !ws || !wsOpen) return;
    sending = true;
    const optimisticMsg: Message = {
      id: -Date.now(),
      sender_type: 'admin',
      content,
      created_at: new Date().toISOString(),
    };
    messages = [...messages, optimisticMsg];
    replyText = '';
    ws.send(JSON.stringify({ type: 'admin_message', conversation_id: selectedConv.id, content }));
    sending = false;
    tick().then(() => scrollToBottom(true));
  }

  async function markAllRead() {
    try {
      await chatPost('/api/chat/admin/mark-all-read/', {});
      conversations = conversations.map((c) => ({ ...c, unread_count: 0 }));
      adminUnreadStore.refresh();
    } catch {
      //
    }
  }

  async function blockConv(conv: Conversation) {
    if (actionLoading) return;
    actionLoading = true;
    try {
      await chatPost(`/api/chat/admin/conversations/${conv.id}/block/`, {});
      conv.is_blocked = true;
      conversations = conversations.map((c) => (c.id === conv.id ? { ...c, is_blocked: true } : c));
    } finally {
      actionLoading = false;
    }
  }

  async function unblockConv(conv: Conversation) {
    if (actionLoading) return;
    actionLoading = true;
    try {
      await chatPost(`/api/chat/admin/conversations/${conv.id}/unblock/`, {});
      conv.is_blocked = false;
      conversations = conversations.map((c) => (c.id === conv.id ? { ...c, is_blocked: false } : c));
    } finally {
      actionLoading = false;
    }
  }

  function askDelete(conv: Conversation) {
    confirmDelete = conv;
  }

  function cancelDelete() {
    confirmDelete = null;
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && confirmDelete) cancelDelete();
  }

  async function doDelete() {
    const conv = confirmDelete;
    if (!conv || actionLoading) return;
    actionLoading = true;
    try {
      await chatDelete(`/api/chat/admin/conversations/${conv.id}/`);
      conversations = conversations.filter((c) => c.id !== conv.id);
      if (selectedConv?.id === conv.id) {
        selectedConv = conversations[0] ?? null;
        messages = selectedConv ? [] : [];
        if (selectedConv) loadMessages(selectedConv);
      }
      confirmDelete = null;
    } finally {
      actionLoading = false;
    }
  }

  let mounted = false;
  $effect(() => {
    setPageMeta({ title: 'Administration', description: 'Gestion des conversations chat' });
  });
  $effect(() => {
    if (!mounted) {
      mounted = true;
      loadConversations();
    }
    return () => {
      ws?.close();
    };
  });
  $effect(() => {
    if (confirmDelete) {
      window.addEventListener('keydown', onKeydown);
      return () => window.removeEventListener('keydown', onKeydown);
    }
  });
</script>

<main class="gestion">
  <h1>Administration — Chat</h1>

  {#if loading}
    <p>Chargement…</p>
  {:else if error}
    <p class="gestion-error">{error}</p>
  {:else}
    <div class="gestion-layout">
      <aside class="gestion-sidebar">
        <div class="gestion-sidebar-actions">
          <button type="button" onclick={markAllRead}>Tout marquer lu</button>
        </div>
        <ul class="gestion-conv-list">
          {#each conversations as conv}
            <li>
              <button
                type="button"
                class="gestion-conv-item"
                class:selected={selectedConv?.id === conv.id}
                class:blocked={conv.is_blocked}
                onclick={() => loadMessages(conv)}
              >
                <span class="gestion-conv-label">{guestLabel(conv)}</span>
                {#if (conv.unread_count || 0) > 0}
                  <span class="gestion-conv-badge">{conv.unread_count}</span>
                {/if}
                {#if conv.last_message}
                  <span class="gestion-conv-preview">{conv.last_message.content?.slice(0, 40)}…</span>
                {/if}
              </button>
            </li>
          {/each}
        </ul>
        {#if conversations.length === 0}
          <p class="gestion-empty">Aucune conversation</p>
        {/if}
      </aside>

      <section class="gestion-main">
        {#if selectedConv}
          <div class="gestion-main-header">
            <h2>{guestLabel(selectedConv)}</h2>
            <p class="gestion-main-meta">
              {#if selectedConv.guest_email}{selectedConv.guest_email}{/if}
              {#if selectedConv.guest_phone} · {selectedConv.guest_phone}{/if}
            </p>
            <div class="gestion-main-actions">
              {#if selectedConv.is_blocked}
                <button type="button" onclick={() => unblockConv(selectedConv!)} disabled={actionLoading}>Débloquer</button>
              {:else}
                <button type="button" onclick={() => blockConv(selectedConv!)} disabled={actionLoading}>Bloquer</button>
              {/if}
              <button type="button" class="gestion-delete" onclick={() => askDelete(selectedConv!)}>Supprimer</button>
            </div>
          </div>

          <div class="gestion-messages" bind:this={messagesContainerEl}>
            {#if loadingMessages}
              <p>Chargement…</p>
            {:else}
              {#each messages as msg (msg.id)}
                <div class="gestion-msg gestion-msg-{msg.sender_type}">
                  <span class="gestion-msg-content">{msg.content}</span>
                  <span class="gestion-msg-time">{formatDate(msg.created_at)}</span>
                </div>
              {/each}
            {/if}
          </div>

          {#if !selectedConv.is_blocked}
            <form class="gestion-reply" onsubmit={(e) => { e.preventDefault(); sendReply(); }}>
              <input
                type="text"
                bind:value={replyText}
                placeholder="Répondre…"
                maxlength="2000"
                disabled={!wsOpen || sending}
              />
              <button type="submit" disabled={!replyText.trim() || !wsOpen || sending}>Envoyer</button>
            </form>
          {:else}
            <p class="gestion-blocked">Cette conversation est bloquée.</p>
          {/if}
        {:else}
          <p class="gestion-select">Sélectionnez une conversation</p>
        {/if}
      </section>
    </div>
  {/if}
</main>

{#if confirmDelete}
  <div
    class="gestion-modal-overlay"
    role="presentation"
    onclick={cancelDelete}
    onkeydown={(e) => e.key === 'Escape' && cancelDelete()}
  >
    <div
      class="gestion-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-delete-title"
      tabindex="-1"
      onclick={(e) => e.stopPropagation()}
    >
      <h2 id="modal-delete-title">Supprimer cette conversation ?</h2>
      <p>Tous les messages seront définitivement supprimés.</p>
      <div class="gestion-modal-actions">
        <button type="button" class="gestion-modal-danger" onclick={doDelete} disabled={actionLoading}>Supprimer</button>
        <button type="button" onclick={cancelDelete}>Annuler</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .gestion {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    align-self: stretch;
    padding: 0 clamp(1rem, 3vw, 2rem);
    font-family: 'Playwrite GB S', cursive;
    box-sizing: border-box;
  }
  .gestion h1 {
    color: #cd5f72;
    margin-bottom: 1rem;
    font-size: clamp(1.25rem, 2vw, 1.5rem);
  }
  .gestion-error {
    color: #c00;
  }
  .gestion-layout {
    display: grid;
    grid-template-columns: minmax(320px, 380px) minmax(420px, 1fr);
    gap: 1.5rem;
    min-height: 60vh;
  }
  @media (max-width: 768px) {
    .gestion-layout {
      grid-template-columns: 1fr;
    }
  }
  .gestion-sidebar {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    border: 1px solid rgba(187, 144, 180, 0.3);
    border-radius: 1rem;
    padding: 1rem;
    background: #fff;
  }
  .gestion-sidebar-actions button {
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    border: 1px solid #bb90b4;
    background: #fff;
    color: #bb90b4;
    cursor: pointer;
    font-family: inherit;
    font-size: 0.9rem;
  }
  .gestion-sidebar-actions button:hover {
    background: #f5f0f4;
  }
  .gestion-conv-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    overflow-y: auto;
  }
  .gestion-conv-item {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
    padding: 0.6rem 0.75rem;
    border: none;
    border-radius: 0.5rem;
    background: #f9f6f8;
    cursor: pointer;
    font-family: inherit;
    text-align: left;
    transition: background 0.2s;
  }
  .gestion-conv-item:hover {
    background: #f0e8ec;
  }
  .gestion-conv-item.selected {
    background: #e8dce5;
    border: 1px solid #bb90b4;
  }
  .gestion-conv-item.blocked {
    opacity: 0.7;
  }
  .gestion-conv-label {
    font-weight: 600;
    color: #333;
  }
  .gestion-conv-badge {
    background: #cd5f72;
    color: white;
    font-size: 0.75rem;
    padding: 0.1rem 0.4rem;
    border-radius: 999px;
    margin-top: 0.25rem;
  }
  .gestion-conv-preview {
    font-size: 0.8rem;
    color: #666;
    margin-top: 0.2rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
  }
  .gestion-empty {
    color: #666;
    font-size: 0.9rem;
    margin: 0.5rem 0 0;
  }
  .gestion-main {
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 400px;
    border: 1px solid rgba(187, 144, 180, 0.3);
    border-radius: 1rem;
    background: #fff;
    overflow: hidden;
  }
  .gestion-main-header {
    padding: 1rem;
    border-bottom: 1px solid rgba(187, 144, 180, 0.25);
    flex-shrink: 0;
  }
  .gestion-main-header h2 {
    margin: 0 0 0.25rem;
    font-size: 1.1rem;
    color: #cd5f72;
  }
  .gestion-main-meta {
    margin: 0 0 0.5rem;
    font-size: 0.85rem;
    color: #666;
  }
  .gestion-main-actions {
    display: flex;
    gap: 0.5rem;
  }
  .gestion-main-actions button {
    padding: 0.35rem 0.75rem;
    border-radius: 0.5rem;
    border: 1px solid #bb90b4;
    background: #fff;
    color: #bb90b4;
    cursor: pointer;
    font-family: inherit;
    font-size: 0.85rem;
  }
  .gestion-main-actions button:hover {
    background: #f5f0f4;
  }
  .gestion-delete {
    border-color: #c00 !important;
    color: #c00 !important;
  }
  .gestion-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    min-height: 200px;
  }
  .gestion-msg {
    max-width: 85%;
    padding: 0.6rem 0.9rem;
    border-radius: 1rem;
  }
  .gestion-msg-admin {
    align-self: flex-end;
    background: #e8e0e6;
    color: #333;
    border-bottom-right-radius: 0.25rem;
  }
  .gestion-msg-guest {
    align-self: flex-start;
    background: #f5f0f4;
    border: 1px solid rgba(187, 144, 180, 0.25);
    border-bottom-left-radius: 0.25rem;
  }
  .gestion-msg-content {
    display: block;
    word-break: break-word;
    font-size: 0.9rem;
  }
  .gestion-msg-time {
    font-size: 0.75rem;
    color: #666;
    margin-top: 0.25rem;
  }
  .gestion-reply {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
    border-top: 1px solid rgba(187, 144, 180, 0.25);
    flex-shrink: 0;
  }
  .gestion-reply input {
    flex: 1;
    padding: 0.6rem 1rem;
    border-radius: 0.75rem;
    border: 1px solid rgba(187, 144, 180, 0.4);
    font-family: inherit;
    font-size: 0.95rem;
  }
  .gestion-reply button {
    padding: 0.6rem 1.25rem;
    border-radius: 0.75rem;
    border: none;
    background: #bb90b4;
    color: white;
    cursor: pointer;
    font-family: inherit;
  }
  .gestion-reply button:hover:not(:disabled) {
    background: #cd5f72;
  }
  .gestion-reply button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .gestion-blocked,
  .gestion-select {
    padding: 2rem;
    text-align: center;
    color: #666;
  }
  .gestion-modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .gestion-modal {
    background: #fff;
    padding: 1.5rem;
    border-radius: 1rem;
    max-width: 400px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  }
  .gestion-modal h2 {
    margin: 0 0 0.5rem;
    font-size: 1.1rem;
    color: #333;
  }
  .gestion-modal p {
    margin: 0 0 1rem;
    font-size: 0.9rem;
    color: #666;
  }
  .gestion-modal-actions {
    display: flex;
    gap: 0.75rem;
  }
  .gestion-modal-actions button {
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    border: 1px solid #888;
    background: #fff;
    cursor: pointer;
    font-family: inherit;
  }
  .gestion-modal-danger {
    background: #c00 !important;
    color: white !important;
    border-color: #c00 !important;
  }
</style>
