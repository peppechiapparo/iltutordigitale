# Copilot Instructions — Il Tutor Digitale

Questo file viene letto automaticamente da GitHub Copilot come contesto di progetto.
Posizione: `.github/copilot-instructions.md`

---

## Progetto

**Il Tutor Digitale** — portale web per canale di tutorial tecnologici italiani.
Creator: Abby | Nicchia: tecnologia per principianti | Pubblico: italiani over 45-65 anni.

---

## Stack tecnico

- **Astro 4.x** (Static Site Generator — output HTML statico)
- **Tailwind CSS 3.x** (utility-first, mobile-first)
- **TypeScript** (strict mode, sempre)
- **Cloudflare Pages** (hosting, deploy automatico da GitHub)
- **GitHub Actions** (CI/CD pipeline)

---

## Convenzioni codice

| Tipo | Convenzione |
|------|-------------|
| Componenti `.astro` | PascalCase: `VideoCard.astro` |
| Pagine `.astro` | kebab-case: `chi-sono.astro` |
| File `.ts` utility | camelCase: `formatDate.ts` |
| File Markdown contenuti | kebab-case: `backup-android.md` |
| Costanti | UPPER_SNAKE_CASE |
| Commenti nel codice | Italiano |
| CSS | Solo classi Tailwind, zero inline style |

---

## Colori Tailwind brand (definiti in tailwind.config.mjs)

```
text-brand-blue        bg-brand-blue        → #185FA5
text-brand-blue-mid    bg-brand-blue-mid    → #378ADD
text-brand-blue-light  bg-brand-blue-light  → #E6F1FB
text-brand-orange      bg-brand-orange      → #EF9F27
text-brand-orange-dk   bg-brand-orange-dk   → #BA7517
text-brand-dark        bg-brand-dark        → #2C2C2A
text-brand-bg          bg-brand-bg          → #F1EFE8
```

---

## Font

- Titoli (H1-H3): `font-heading` → Nunito Bold
- Corpo testo: `font-sans` → Inter Regular
- Testo minimo: 17px (`text-base` custom) — il pubblico ha 45-65 anni

---

## Accessibilità (obbligatoria)

- Sempre `alt=""` sulle immagini (descrittivo o `alt=""` se decorativa)
- Sempre `aria-label` su bottoni senza testo visibile
- Contrasto minimo WCAG AA (4.5:1 per testo normale)
- `focus-visible` stile visibile (definito in global.css)
- Mai rimuovere l'outline di focus

---

## Performance

- Immagini: usa `<Image>` di Astro invece di `<img>` nativo
- Font: `font-display: swap` in CSS
- Mai importare librerie JavaScript pesanti senza valutare alternative leggere
- Lazy loading su immagini e video embed YouTube

---

## Struttura cartelle essenziale

```
src/
├── components/   ← componenti riutilizzabili (.astro)
├── layouts/      ← layout pagine (BaseLayout, BlogLayout)
├── pages/        ← ogni file = una URL
├── content/      ← contenuti Markdown con schema TypeScript
├── data/         ← JSON statici (video, prodotti, link)
├── styles/       ← global.css
└── utils/        ← funzioni TypeScript pure
```

---

## Regole di sicurezza

- **Mai** committare `.env` o chiavi API
- Variabili sensibili: solo in `.env.local` (locale) o Cloudflare Pages env vars (produzione)
- Form con validazione sia lato client che lato server (Cloudflare Worker)

---

## Mobile-first

Tutto il CSS parte da mobile (375px) e usa breakpoint Tailwind per desktop:
- `sm:` → 640px
- `md:` → 768px  
- `lg:` → 1024px
- `xl:` → 1280px

Il pubblico usa principalmente smartphone — il mobile non è mai secondario.

---

## Documentazione di riferimento

Tutti i file nella cartella `tutor-digitale-docs/`:
- `01-ARCHITETTURA.md` — decisioni stack
- `03-STRUTTURA-PROGETTO.md` — struttura file completa
- `05-PORTALE-SPEC.md` — specifiche funzionali pagine
- `06-BRAND-ASSETS.md` — colori, font, logo
- `09-DEPLOY-WORKFLOW.md` — CI/CD e workflow git
