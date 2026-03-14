<script lang="ts">
  import * as api from '../lib/api';
  import type { Categorie, Vetement } from '../lib/api';
  import { auth } from '../stores/auth';
  import { showToast } from '../lib/toastStore';
  import { setPageMeta } from '../lib/pageMeta';

  let categories = $state<Categorie[]>([]);
  let vetements = $state<Vetement[]>([]);
  let loading = $state(true);
  let error = $state('');
  let activeCategory = $state<number | null>(null);
  let modalOpen = $state(false);
  let uploading = $state(false);
  let uploadError = $state('');
  let selectedFiles = $state<File[]>([]);
  let selectedCategorieId = $state<string>('');
  let editingId = $state<number | null>(null);
  let editName = $state('');
  let showScrollTop = $state(false);
  let deleteConfirmId = $state<number | null>(null);
  let loadedImages = $state<Set<number>>(new Set());

  let filteredVetements = $derived(
    activeCategory === null
      ? vetements
      : vetements.filter((v) => v.categorie_id === activeCategory)
  );

  async function load() {
    loading = true;
    error = '';
    try {
      const [cats, vets] = await Promise.all([api.fetchCategories(), api.fetchVetements()]);
      categories = cats;
      vetements = vets;
      if (cats.length) selectedCategorieId = String(cats[0].id);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Erreur chargement';
    } finally {
      loading = false;
    }
  }

  function selectCategory(id: number) {
    if (activeCategory === id) activeCategory = null;
    else activeCategory = id;
  }

  async function handleUpload(e: Event) {
    const form = e.target as HTMLFormElement;
    await import('../lib/csrf').then((m) => m.ensureCsrf());
    const fd = new FormData();
    const catId = (form.querySelector('[name="categorie"]') as HTMLSelectElement)?.value;
    const input = form.querySelector('[name="image"]') as HTMLInputElement;
    if (!catId || !input?.files?.length) return;
    for (const file of input.files) fd.append('image', file);
    fd.append('categorie', catId);
    uploading = true;
    uploadError = '';
    try {
      await api.uploadImages(fd);
      modalOpen = false;
      selectedFiles = [];
      await load();
      showToast('Images ajoutées avec succès', 'success');
    } catch (e) {
      uploadError = e instanceof Error ? e.message : 'Erreur upload';
      showToast(uploadError, 'error');
    } finally {
      uploading = false;
    }
  }

  function startEdit(v: Vetement) {
    editingId = v.id;
    editName = v.nom;
  }

  async function saveEdit() {
    if (editingId === null) return;
    try {
      await api.updateVetementName(editingId, editName);
      vetements = vetements.map((x) => (x.id === editingId ? { ...x, nom: editName } : x));
      editingId = null;
      showToast('Nom mis à jour', 'success');
    } catch (_) {
      showToast('Erreur lors de la mise à jour', 'error');
    }
  }

  function askRemove(id: number) {
    deleteConfirmId = id;
  }

  async function confirmRemove() {
    if (deleteConfirmId === null) return;
    const id = deleteConfirmId;
    deleteConfirmId = null;
    try {
      await api.deleteVetement(id);
      vetements = vetements.filter((x) => x.id !== id);
      showToast('Vêtement supprimé', 'success');
    } catch (_) {
      showToast('Erreur lors de la suppression', 'error');
    }
  }

  function cancelRemove() {
    deleteConfirmId = null;
  }

  function fileChange(e: Event) {
    const input = e.target as HTMLInputElement;
    selectedFiles = input.files ? Array.from(input.files) : [];
  }

  $effect(() => {
    setPageMeta({ title: 'Accueil', description: 'Découvrez la collection Printemps & Été de Creabyemma' });
  });
  $effect(() => {
    load();
  });

  function onScroll() {
    showScrollTop = window.scrollY > 200;
  }

  $effect(() => {
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  });

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      if (deleteConfirmId !== null) cancelRemove();
      else if (modalOpen) modalOpen = false;
    }
  }
  $effect(() => {
    const hasModal = deleteConfirmId !== null || modalOpen;
    if (hasModal) {
      window.addEventListener('keydown', onKeydown);
      return () => window.removeEventListener('keydown', onKeydown);
    }
  });
</script>

<main>
  <h1 class="sr-only">Bienvenue chez Creabyemma - Boutique de vêtements tendance</h1>

  {#if loading}
    <div class="skeleton-container">
      <div class="skeleton-categories"></div>
      <div class="skeleton-grid">
        {#each Array(6) as _}
          <div class="skeleton-card">
            <div class="skeleton-img"></div>
            <div class="skeleton-text"></div>
          </div>
        {/each}
      </div>
    </div>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="category-buttons">
      {#each categories as cat}
        <button
          type="button"
          class="category-button"
          class:active={activeCategory === cat.id}
          onclick={() => selectCategory(cat.id)}
        >
          {#if cat.logo_url}
            <img src={cat.logo_url} alt={cat.nom} class="category-logo" />
          {:else}
            <span>{cat.nom}</span>
          {/if}
        </button>
      {/each}
    </div>

    {#if $auth}
      <div class="add-button-container">
        <button type="button" class="add-button" onclick={() => (modalOpen = true)}>Ajouter</button>
      </div>
    {/if}

    <div class="grid-container">
      {#each filteredVetements as v}
        <div class="grid-item" data-categorie={v.categorie_id}>
          <div class="img-container">
            <div class="img-placeholder" class:loaded={loadedImages.has(v.id)} aria-hidden="true"></div>
            <img
              src={v.image_url}
              alt={v.nom}
              class="grid-item-img"
              class:loaded={loadedImages.has(v.id)}
              loading="lazy"
              decoding="async"
              onload={() => loadedImages = new Set(loadedImages).add(v.id)}
            />
            {#if $auth}
              <button
                type="button"
                class="delete-icon-grid"
                aria-label="Supprimer"
                onclick={() => askRemove(v.id)}
              >
                <img src="/static/images/trash.avif" alt="" />
              </button>
            {/if}
          </div>
          <div class="info-container">
            <h2>
              {#if editingId === v.id}
                <input
                  type="text"
                  class="edit-input"
                  bind:value={editName}
                  onkeydown={(e) => e.key === 'Enter' && saveEdit()}
                />
                <button type="button" class="save-btn" onclick={saveEdit}>
                  <img src="/static/images/save.avif" alt="Enregistrer" class="save-icon" />
                </button>
              {:else}
                <span class="vetement-nom">{v.nom}</span>
                {#if $auth}
                  <button
                    type="button"
                    class="edit-icon"
                    aria-label="Modifier"
                    onclick={() => startEdit(v)}
                  >
                    <img src="/static/images/edit.avif" alt="" class="edit-icon" />
                  </button>
                {/if}
              {/if}
            </h2>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <button
    type="button"
    id="scroll-to-top"
    title="Remonter"
    class:visible={showScrollTop}
    onclick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
  >
    ↑
  </button>
</main>

{#if deleteConfirmId !== null}
  <div class="modal modal-confirm" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
    <div class="modal-content modal-content--small">
      <h2 id="confirm-title">Supprimer ce vêtement ?</h2>
      <div class="modal-actions">
        <button type="button" class="modal-submit modal-submit--danger" onclick={confirmRemove}>Oui</button>
        <button type="button" class="modal-cancel" onclick={cancelRemove}>Annuler</button>
      </div>
    </div>
  </div>
{/if}

{#if $auth && modalOpen}
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-content">
      <button type="button" class="close-button" aria-label="Fermer" onclick={() => (modalOpen = false)}>&times;</button>
      <h2 id="modal-title">Ajouter des images</h2>
      <form onsubmit={(e) => { e.preventDefault(); handleUpload(e); }}>
        <div class="modal-image">
          <label for="image" class="file-upload-label">
            <img src="/static/images/upload_icon.avif" alt="" class="upload-icon" />
          </label>
          <input type="file" id="image" name="image" accept="image/*" multiple required onchange={fileChange} />
          <p>{selectedFiles.length} fichier(s) sélectionné(s)</p>
        </div>
        <div>
          <label for="categorie">Catégorie</label>
          <select name="categorie" id="categorie" bind:value={selectedCategorieId}>
            {#each categories as c}
              <option value={c.id}>{c.nom}</option>
            {/each}
          </select>
        </div>
        {#if uploadError}<p class="error">{uploadError}</p>{/if}
        <button type="submit" class="modal-submit" disabled={uploading || selectedFiles.length === 0}>
          {uploading ? 'Envoi…' : 'Valider'}
        </button>
      </form>
    </div>
  </div>
{/if}

<style>
  .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); }
  .error { color: #c00; }
  #scroll-to-top { display: none; }
  #scroll-to-top.visible { display: block; }
  .delete-icon-grid img, .edit-icon img, .save-icon { width: 100%; height: 100%; object-fit: contain; }
  .modal-content--small { width: auto; min-width: 260px; }
  .modal-actions { display: flex; gap: 1rem; }
  .modal-submit--danger { background-color: #c00; }
  .modal-cancel { background: #888; color: white; border: none; padding: 8px 16px; border-radius: 16px; cursor: pointer; }

  .skeleton-container { width: 100%; max-width: 1200px; padding: 0 1rem; }
  .skeleton-categories {
    height: 3rem;
    background: linear-gradient(110deg, #ebe0e9 25%, #e3d5e1 50%, #ebe0e9 75%);
    background-size: 200% 100%;
    animation: skeleton 1.2s ease-in-out infinite;
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }
  .skeleton-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 280px), 1fr));
    gap: clamp(1.25rem, 4vw, 2rem);
  }
  .skeleton-card {
    background: #fff;
    border-radius: 1rem;
    overflow: hidden;
    box-shadow: 0 0.25rem 1rem rgba(187, 144, 180, 0.15);
  }
  .skeleton-img {
    aspect-ratio: 3 / 4;
    background: linear-gradient(110deg, #ebe0e9 25%, #e3d5e1 50%, #ebe0e9 75%);
    background-size: 200% 100%;
    animation: skeleton 1.2s ease-in-out infinite;
  }
  .skeleton-text {
    height: 2rem;
    margin: 1rem;
    background: linear-gradient(110deg, #ebe0e9 25%, #e3d5e1 50%, #ebe0e9 75%);
    background-size: 200% 100%;
    animation: skeleton 1.2s ease-in-out infinite;
    border-radius: 0.25rem;
    max-width: 60%;
  }
  @keyframes skeleton {
    to { background-position: 200% 0; }
  }
</style>
