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
  /** Numero WhatsApp internazionale senza + (es: "393401234567"). Lascia vuoto per disabilitare il link. */
  whatsapp: '',
  description:
    'Tutorial di tecnologia semplici e chiari per principianti: smartphone, PC, WhatsApp, sicurezza online. Spiegati passo dopo passo, senza fretta e senza parole difficili.',
  ogImage: '/og-image.jpg',
} as const;

export type SiteCategory = 'smartphone' | 'pc' | 'sicurezza' | 'whatsapp' | 'app';

export const CATEGORIES: Record<SiteCategory, { label: string; emoji: string; description: string }> = {
  smartphone: { label: 'Smartphone',    emoji: '📱', description: 'Come usare il telefono, le app e le impostazioni di base' },
  pc:         { label: 'PC e Internet', emoji: '💻', description: 'Navigare online, usare email e programmi sul computer' },
  whatsapp:   { label: 'WhatsApp',      emoji: '💬', description: 'Messaggi, foto, videochiamate e gruppi con chi ami' },
  sicurezza:  { label: 'Sicurezza',     emoji: '🔒', description: 'Proteggerti online, gestire password e riconoscere le truffe' },
  app:        { label: 'App utili',     emoji: '🧩', description: 'Le migliori app gratuite per semplificare la vita di ogni giorno' },
};
