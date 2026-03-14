/**
 * Met à jour le titre et les meta pour le SEO (par route).
 */
const DEFAULT_TITLE = 'Creabyemma - Boutique de vêtements';
const DEFAULT_DESC = 'Creabyemma - Boutique de vêtements tendance';

export function setPageMeta(options: { title?: string; description?: string; image?: string }) {
  if (typeof document === 'undefined') return;
  document.title = options.title ? `${options.title} | Creabyemma` : DEFAULT_TITLE;

  let desc = document.querySelector('meta[name="description"]');
  const content = options.description ?? DEFAULT_DESC;
  if (!desc) {
    desc = document.createElement('meta');
    desc.setAttribute('name', 'description');
    document.head.appendChild(desc);
  }
  desc.setAttribute('content', content);

  // Open Graph
  const ogTitle = document.querySelector('meta[property="og:title"]') ?? document.createElement('meta');
  if (!ogTitle.getAttribute('property')) ogTitle.setAttribute('property', 'og:title');
  ogTitle.setAttribute('content', document.title);
  if (!document.querySelector('meta[property="og:title"]')) document.head.appendChild(ogTitle);

  const ogDesc = document.querySelector('meta[property="og:description"]') ?? document.createElement('meta');
  if (!ogDesc.getAttribute('property')) ogDesc.setAttribute('property', 'og:description');
  ogDesc.setAttribute('content', content);
  if (!document.querySelector('meta[property="og:description"]')) document.head.appendChild(ogDesc);
}
