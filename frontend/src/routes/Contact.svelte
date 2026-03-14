<script lang="ts">
  import { openChat } from '../lib/chatOpenStore';
  import { setPageMeta } from '../lib/pageMeta';

  // Images du magasin : à servir depuis public ou le backend
  $effect(() => {
    setPageMeta({ title: 'Contact', description: 'Contactez Creabyemma - Téléphone, réseaux sociaux et chat' });
  });

  const magasinImages = [
    '/static/images/magasin1.avif',
    '/static/images/magasin2.avif',
    '/static/images/magasin3.avif',
    '/static/images/magasin4.avif',
  ];
</script>

<main>
  <div class="contact-info">
    <p>📞 <a href="tel:+330228293624">02 28 29 36 24</a></p>
    <p>Vous pouvez également m'envoyer un message sur mes réseaux sociaux ou via le chat.</p>
    <button type="button" class="contact-chat-btn" onclick={openChat}>💬 Ouvrir le chat</button>
    <div class="social-icons">
      <a href="https://facebook.com/creabyemma" target="_blank" rel="noopener noreferrer">
        <img src="/static/images/facebook-circle-icon.avif" alt="Facebook" />
      </a>
      <a href="https://instagram.com/creabyemma" target="_blank" rel="noopener noreferrer">
        <img src="/static/images/instagram-circle-icon.avif" alt="Instagram" />
      </a>
    </div>
  </div>
  <div class="magasin">
    {#each magasinImages as src}
      <img src={src} alt="Intérieur du magasin" class="magasin-img" />
    {/each}
  </div>
</main>
