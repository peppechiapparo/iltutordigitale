# 05 — Specifiche Funzionali del Portale

> Estende la bozza con: blocchi AEO (FAQ), lead magnet, struttura tutorial SEO-friendly.

## Pagine

### Homepage (`/`)
1. **Hero** — headline forte, foto creator, CTA "Guarda i tutorial →"
2. **Problema/Soluzione** — "Hai paura della tecnologia? Sei nel posto giusto."
3. **Video in evidenza** — 3 video più visti (thumbnail + link, lazy)
4. **Chi sono** — bio breve, foto, approccio didattico
5. **Prodotti consigliati** — 3-4 affiliate con disclosure
6. **Social links** — bottoni grandi (YouTube, Facebook, Instagram, TikTok)
7. **Newsletter** — form con lead magnet ("Scarica gratis: Guida Smartphone per Principianti")
8. **Ultimi articoli blog** — 3 recenti

### Tutorial (`/tutorial` + `/tutorial/[slug]`)
- Filtri categoria: Smartphone / PC / WhatsApp / Sicurezza / App
- Card: thumbnail, badge categoria, titolo (max 2 righe), durata, data
- Pagina singola: embed YouTube + **sommario scritto + passi numerati** (SEO) +
  **blocco FAQ** (AEO, vedi `10`) + affiliate correlati + link altri video + form domanda

### Blog (`/blog` + `/blog/[...slug]`)
Ogni articolo: H1 con keyword, meta description ≤160, hero+alt, ≥800 parole (target 1200-1500),
video correlato, ≥2 link interni, **FAQ schema**, CTA finale, `Article` structured data.

### Prodotti (`/prodotti`)
- Prodotti digitali (Gumroad/Payhip) + smartphone/accessori affiliate + app gratuite consigliate
- Ogni item: immagine, nome, prezzo, CTA, **nota disclosure affiliate** (trasparenza obbligatoria)

### Chi sono (`/chi-sono`)
Foto, storia, mission, cosa trovi sul canale, **media kit PDF** scaricabile, contatti.

### Contatti (`/contatti`)
Form: Nome*, Email*, Tipo richiesta (dropdown), Messaggio*, **consenso privacy***.
Backend: Cloudflare Worker → email a `info@<dominio>`, **oppure** Web3Forms/Formspree.

### Legali (`/privacy`, `/cookie`)
Generati con Iubenda (base gratuito) o equivalente. Link in footer. Vedi `11`.

---

## Componenti UI — specifiche

- **Header**: logo + nav + CTA "Iscriviti al canale"; mobile hamburger; sticky; bordo blu leggero.
- **Footer**: logo+tagline+social / link utili / newsletter mini / bottom bar (copyright, privacy,
  cookie, P.IVA quando disponibile); sfondo `brand-dark`.
- **VideoCard**: thumbnail lazy, badge categoria, titolo (ellipsis 2 righe), durata, data, hover lift.
- **Newsletter form**: lead magnet chiaro, email + "Scarica gratis", microcopy "Niente spam",
  provider Brevo con **double opt-in**.
- **FaqBlock** (nuovo): rende `faq[]` del contenuto come accordion + inietta `FAQPage` schema.

---

## Accessibilità (requisito, non opzionale)

- Testo minimo **17px**; mai sotto 13px.
- Contrasto **WCAG AA** (4.5:1) minimo; preferire AAA dove possibile.
- `aria-label` su bottoni icona; `alt` descrittivo o `alt=""` se decorativa.
- `focus-visible` sempre visibile (3px outline arancione); mai rimuovere l'outline.
- Skip-link "Vai al contenuto"; navigazione completa da tastiera.
- Target touch ≥44px (pubblico over 45 su mobile).

---

## Performance targets

| Metrica | Target |
|---------|--------|
| Lighthouse Performance | > 90 |
| Lighthouse SEO | 100 |
| Lighthouse Accessibility | > 95 |
| First Contentful Paint | < 1.5s |
| Core Web Vitals | Pass |

Tecniche: `<Image>` di Astro (WebP), `font-display: swap`, lazy su immagini/embed,
zero JS non necessario (islands solo dove serve).
