/**
 * Dati di progetto centralizzati.
 * Fonte: docs/01-VISIONE-STRATEGIA.md (variabili di progetto).
 */
export const SITE = {
  name: 'Il Tutor Digitale',
  tagline: 'Tecnologia per tutti — senza paura',
  creator: 'Giuseppe',
  url: import.meta.env.PUBLIC_SITE_URL ?? 'https://tutordigitale.com',
  email: 'info@tutordigitale.com',
  description:
    'Tutorial di tecnologia semplici e chiari per principianti: smartphone, PC, WhatsApp, sicurezza online. Spiegati passo dopo passo, senza fretta e senza parole difficili.',
  ogImage: '/og-image.jpg',
} as const;

export type SiteCategory = 'smartphone' | 'pc' | 'sicurezza' | 'whatsapp' | 'app';

export const CATEGORIES: Record<SiteCategory, { label: string; emoji: string }> = {
  smartphone: { label: 'Smartphone', emoji: '📱' },
  pc: { label: 'PC e Internet', emoji: '💻' },
  whatsapp: { label: 'WhatsApp', emoji: '💬' },
  sicurezza: { label: 'Sicurezza', emoji: '🔒' },
  app: { label: 'App utili', emoji: '🧩' },
};
