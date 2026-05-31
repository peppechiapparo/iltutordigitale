# 03 — Struttura del Progetto

> Monorepo: il **portale** (Fase 1) e il **content engine** (Fase 2, opzionale) convivono nello
> stesso repository in cartelle separate. La Fase 2 non viene creata finché non serve.

```
il-tutor-digitale/
│
├── .github/
│   ├── copilot-instructions.md      ← contesto Copilot (vedi 02/06)
│   ├── agents/                      ← agenti VS Code del progetto (vedi 13)
│   ├── skills/                      ← skill di progetto (vedi 13)
│   └── workflows/
│       └── deploy.yml               ← CI/CD Cloudflare Pages
│
├── docs/                            ← QUESTA documentazione (fonte di verità)
│
├── web/                             ← PORTALE ASTRO (Fase 1)
│   ├── public/
│   │   ├── favicon.ico
│   │   ├── logo.svg / logo-white.svg
│   │   ├── og-image.jpg             ← 1200x630
│   │   └── fonts/ (Nunito-Bold.woff2, Inter-Regular.woff2)
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/ (Header, Footer, Navigation)
│   │   │   ├── ui/ (Button, Card, Badge, VideoEmbed)
│   │   │   ├── sections/ (Hero, FeaturedVideos, Newsletter, ProductCard, SocialLinks)
│   │   │   └── seo/ (SEOHead, FaqSchema, ArticleSchema)
│   │   ├── layouts/ (BaseLayout, BlogLayout, VideoLayout)
│   │   ├── pages/
│   │   │   ├── index.astro          ← /
│   │   │   ├── chi-sono.astro
│   │   │   ├── tutorial/ (index, [slug])
│   │   │   ├── blog/ (index, [...slug])
│   │   │   ├── prodotti.astro
│   │   │   ├── contatti.astro
│   │   │   ├── privacy.astro / cookie.astro
│   │   │   └── rss.xml.js
│   │   ├── content/
│   │   │   ├── config.ts            ← schema collezioni (blog, tutorial)
│   │   │   ├── blog/ (*.md)
│   │   │   └── tutorial/ (*.md)
│   │   ├── data/ (videos.json, products.json, social-links.json)
│   │   ├── styles/global.css
│   │   └── utils/ (formatDate.ts, generateSlug.ts, seo.ts)
│   ├── astro.config.mjs
│   ├── tailwind.config.mjs
│   ├── tsconfig.json
│   ├── package.json
│   └── .env.local                   ← NON su git
│
└── engine/                          ← CONTENT ENGINE PYTHON (Fase 2 — creare quando serve)
    ├── src/tutor/
    │   ├── agents/ (base.py, script.py, seo_aeo.py, calendar.py)
    │   ├── adapters/ (llm.py, notifier.py, youtube.py, search_console.py)
    │   ├── tools/ (content_tools.py)
    │   └── core/ (db.py, scheduler.py, config.py, logging.py)
    ├── migrations/ (001_*.sql)
    ├── docker-compose.yml
    └── pyproject.toml
```

> Nota: nella bozza la root era direttamente il progetto Astro. Qui isoliamo il portale in `web/`
> per permettere la coesistenza con `engine/` senza conflitti di build/deploy.

---

## Config chiave

### `web/astro.config.mjs`
```javascript
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import react from '@astrojs/react';

export default defineConfig({
  site: process.env.PUBLIC_SITE_URL ?? 'https://example.com',
  integrations: [tailwind(), sitemap(), react()],
  output: 'static',
});
```

### `web/tailwind.config.mjs` (estratto brand — vedi 06)
```javascript
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  theme: { extend: {
    colors: { brand: {
      blue:'#185FA5','blue-mid':'#378ADD','blue-light':'#E6F1FB',
      orange:'#EF9F27','orange-dk':'#BA7517','orange-lt':'#FAC775',
      dark:'#2C2C2A', mid:'#888780', bg:'#F1EFE8' } },
    fontFamily: { sans:['Inter','system-ui','sans-serif'], heading:['Nunito','system-ui','sans-serif'] },
    fontSize: { base:['17px','1.7'], lg:['19px','1.65'], xl:['22px','1.5'] },
  } },
  plugins: [],
};
```

### Schema contenuti `web/src/content/config.ts`
```typescript
import { defineCollection, z } from 'astro:content';

const baseFields = {
  title: z.string(),
  description: z.string(),
  pubDate: z.coerce.date(),
  updatedDate: z.coerce.date().optional(),
  category: z.enum(['smartphone','pc','sicurezza','whatsapp','app']),
  tags: z.array(z.string()),
  heroImage: z.string().optional(),
  youtubeId: z.string().optional(),
  faq: z.array(z.object({ q: z.string(), a: z.string() })).optional(), // AEO
  affiliate: z.array(z.object({ name: z.string(), url: z.string(), price: z.string().optional() })).optional(),
};

const blog = defineCollection({ type:'content', schema: z.object(baseFields) });
const tutorial = defineCollection({ type:'content', schema: z.object(baseFields) });
export const collections = { blog, tutorial };
```

> Aggiunta rispetto alla bozza: campo `faq` per generare **FAQ structured data** (AEO, vedi `10`).

---

## Naming conventions

| Tipo | Convenzione | Esempio |
|------|-------------|---------|
| Componenti Astro | PascalCase | `VideoCard.astro` |
| Pagine | kebab-case | `chi-sono.astro` |
| Markdown contenuti | kebab-case | `backup-android.md` |
| Utility TS | camelCase | `formatDate.ts` |
| Costanti | UPPER_SNAKE | `SITE_URL` |
| Commenti codice | italiano | — |
