# 03 — Struttura del Progetto

## Struttura cartelle completa

```
il-tutor-digitale/
│
├── .github/
│   ├── copilot-instructions.md     ← istruzioni per GitHub Copilot
│   └── workflows/
│       └── deploy.yml              ← CI/CD Cloudflare Pages
│
├── tutor-digitale-docs/            ← questa documentazione
│   ├── README.md
│   ├── 01-ARCHITETTURA.md
│   └── ...
│
├── public/                         ← file statici (non processati)
│   ├── favicon.ico
│   ├── logo.svg
│   ├── logo-white.svg
│   ├── og-image.jpg               ← immagine Open Graph (1200x630)
│   └── fonts/
│       ├── Nunito-Bold.woff2
│       └── Inter-Regular.woff2
│
├── src/
│   ├── components/                 ← componenti riutilizzabili
│   │   ├── layout/
│   │   │   ├── Header.astro
│   │   │   ├── Footer.astro
│   │   │   └── Navigation.astro
│   │   ├── ui/
│   │   │   ├── Button.astro
│   │   │   ├── Card.astro
│   │   │   ├── Badge.astro
│   │   │   └── VideoEmbed.astro
│   │   ├── sections/
│   │   │   ├── Hero.astro
│   │   │   ├── FeaturedVideos.astro
│   │   │   ├── Newsletter.astro
│   │   │   ├── ProductCard.astro
│   │   │   └── SocialLinks.astro
│   │   └── seo/
│   │       └── SEOHead.astro
│   │
│   ├── layouts/
│   │   ├── BaseLayout.astro        ← layout base con Header/Footer
│   │   ├── BlogLayout.astro        ← layout per articoli blog
│   │   └── VideoLayout.astro       ← layout per pagine tutorial
│   │
│   ├── pages/                      ← ogni file = una URL
│   │   ├── index.astro             ← / (homepage)
│   │   ├── chi-sono.astro          ← /chi-sono
│   │   ├── tutorial/
│   │   │   ├── index.astro         ← /tutorial (lista tutti)
│   │   │   ├── smartphone.astro    ← /tutorial/smartphone
│   │   │   ├── pc.astro            ← /tutorial/pc
│   │   │   ├── whatsapp.astro      ← /tutorial/whatsapp
│   │   │   └── sicurezza.astro     ← /tutorial/sicurezza
│   │   ├── blog/
│   │   │   ├── index.astro         ← /blog (lista articoli)
│   │   │   └── [...slug].astro     ← /blog/titolo-articolo (dinamico)
│   │   ├── prodotti.astro          ← /prodotti (guide PDF, corsi)
│   │   ├── contatti.astro          ← /contatti
│   │   └── rss.xml.js              ← feed RSS automatico
│   │
│   ├── content/                    ← contenuti in Markdown
│   │   ├── config.ts               ← schema collezioni
│   │   ├── blog/                   ← articoli blog (.md)
│   │   │   ├── come-fare-backup-android.md
│   │   │   ├── truffe-whatsapp-2026.md
│   │   │   └── ...
│   │   └── tutorial/               ← guide tutorial (.md)
│   │       ├── backup-android.md
│   │       └── ...
│   │
│   ├── data/                       ← dati statici JSON
│   │   ├── videos.json             ← lista video YouTube con metadati
│   │   ├── products.json           ← prodotti affiliate Amazon
│   │   └── social-links.json       ← link a tutti i social
│   │
│   ├── styles/
│   │   └── global.css              ← stili globali + variabili CSS
│   │
│   └── utils/
│       ├── formatDate.ts           ← formatta date in italiano
│       ├── generateSlug.ts         ← genera slug da titolo
│       └── seo.ts                  ← helper meta tag SEO
│
├── astro.config.mjs                ← configurazione Astro
├── tailwind.config.mjs             ← configurazione Tailwind
├── tsconfig.json                   ← configurazione TypeScript
├── package.json
├── .env.local                      ← variabili locali (NON su git)
└── .gitignore
```

---

## File di configurazione

### `astro.config.mjs`
```javascript
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';

export default defineConfig({
  site: 'https://iltutordigitale.it',
  integrations: [
    tailwind(),
    sitemap(),
    react(),
  ],
  output: 'static',
});
```

### `tailwind.config.mjs`
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: {
          blue:        '#185FA5',
          'blue-mid':  '#378ADD',
          'blue-light':'#E6F1FB',
          orange:      '#EF9F27',
          'orange-dk': '#BA7517',
          'orange-lt': '#FAC775',
          dark:        '#2C2C2A',
          mid:         '#888780',
          bg:          '#F1EFE8',
        },
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Nunito', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        // Scala più grande per leggibilità over 45
        base: ['17px', '1.7'],
        lg:   ['19px', '1.65'],
        xl:   ['22px', '1.5'],
      },
    },
  },
  plugins: [],
};
```

### `src/styles/global.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Font locali */
@font-face {
  font-family: 'Nunito';
  src: url('/fonts/Nunito-Bold.woff2') format('woff2');
  font-weight: 700;
  font-display: swap;
}

@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter-Regular.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}

/* Variabili CSS brand */
:root {
  --color-primary: #185FA5;
  --color-accent:  #EF9F27;
  --color-dark:    #2C2C2A;
  --color-bg:      #F1EFE8;
}

/* Accessibilità — testo minimo 17px per over 45 */
body {
  font-size: 17px;
  line-height: 1.7;
  color: var(--color-dark);
  background: #ffffff;
}

/* Focus visibile per accessibilità */
:focus-visible {
  outline: 3px solid var(--color-accent);
  outline-offset: 2px;
}
```

---

## Schema contenuti (`src/content/config.ts`)

```typescript
import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title:       z.string(),
    description: z.string(),
    pubDate:     z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    category:    z.enum(['smartphone', 'pc', 'sicurezza', 'whatsapp', 'app']),
    tags:        z.array(z.string()),
    heroImage:   z.string().optional(),
    youtubeId:   z.string().optional(), // ID video YouTube correlato
    affiliate:   z.array(z.object({
      name:  z.string(),
      url:   z.string(),
      price: z.string().optional(),
    })).optional(),
  }),
});

export const collections = { blog };
```

---

## Naming conventions

| Tipo | Convenzione | Esempio |
|------|-------------|---------|
| Componenti Astro | PascalCase | `VideoCard.astro` |
| Pagine | kebab-case | `chi-sono.astro` |
| File Markdown | kebab-case | `backup-android.md` |
| File TypeScript utility | camelCase | `formatDate.ts` |
| Costanti | UPPER_SNAKE | `SITE_URL` |
| Classi Tailwind | nessuna convenzione aggiuntiva | usa classi standard |
| Variabili CSS | `--color-nome`, `--font-nome` | `--color-primary` |

---

## Dati statici — formato

### `src/data/videos.json`
```json
[
  {
    "id": "video-001",
    "youtubeId": "dQw4w9WgXcQ",
    "title": "Come fare il backup del telefono Android",
    "description": "Guida passo per passo per salvare tutti i tuoi dati",
    "category": "smartphone",
    "duration": "11:24",
    "pubDate": "2026-06-01",
    "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "tags": ["backup", "android", "smartphone", "dati"],
    "featured": true
  }
]
```

### `src/data/products.json`
```json
[
  {
    "id": "prod-001",
    "name": "Smartphone Samsung Galaxy A15",
    "description": "Ottimo per chi inizia, schermo grande e batteria lunga",
    "amazonUrl": "https://amzn.to/XXXXXXX",
    "price": "189€",
    "category": "smartphone",
    "rating": 4.5,
    "recommended": true,
    "youtubeReviewId": "ID-VIDEO-RECENSIONE"
  }
]
```
