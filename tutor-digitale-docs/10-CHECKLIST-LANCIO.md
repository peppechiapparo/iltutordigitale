# 10 — Checklist di Lancio

Traccia i progressi mettendo `x` nelle checkbox: `- [x] Completato`

---

## FASE 0 — Preparazione (Settimana 1)

### Dominio e account
- [ ] Acquistato dominio `iltutordigitale.it` (o .com) su Aruba o Cloudflare Registrar
- [ ] Creato account Cloudflare (cloudflare.com)
- [ ] Dominio agganciato a Cloudflare (nameserver configurati)
- [ ] Creato account GitHub Pro
- [ ] GitHub Copilot Pro attivato e funzionante in VSCode
- [ ] Creato account Anthropic (claude.ai) — piano Pro attivo

### Ambiente di sviluppo
- [ ] Node.js v20 installato (`node --version`)
- [ ] Git installato e configurato (`git config --global user.email`)
- [ ] VSCode installato con tutte le estensioni (vedi `02-SETUP-AMBIENTE.md`)
- [ ] Repository GitHub `il-tutor-digitale` creato (private)
- [ ] File `.github/copilot-instructions.md` creato e committato
- [ ] Progetto Astro inizializzato (`npm create astro@latest`)
- [ ] Tailwind CSS configurato e funzionante
- [ ] `.env.local` creato con tutte le variabili
- [ ] `.gitignore` aggiornato con `.env*`

### Cloudflare Pages
- [ ] Progetto Cloudflare Pages creato e collegato a GitHub
- [ ] Build settings configurati (comando: `npm run build`, output: `dist`)
- [ ] Environment variables inserite su Cloudflare
- [ ] Dominio custom collegato a Cloudflare Pages
- [ ] HTTPS automatico attivo (SSL/TLS)
- [ ] Cloudflare Email Routing configurato (`info@iltutordigitale.it`)
- [ ] Cloudflare Web Analytics attivato

### GitHub Actions
- [ ] File `.github/workflows/deploy.yml` creato
- [ ] Tutti i secrets aggiunti su GitHub (CLOUDFLARE_API_TOKEN, etc.)
- [ ] Primo deploy automatico riuscito (status verde)

---

## FASE 1 — Social media (Settimana 1-2)

### Preparazione brand
- [ ] Foto profilo professionale scattata (sfondo blu #185FA5)
- [ ] Logo creato in Canva (tutte le varianti — vedi `06-BRAND-ASSETS.md`)
- [ ] Copertine create per tutte le piattaforme
- [ ] Font Nunito e Inter scaricati e installati in Canva
- [ ] Template Canva creati: thumbnail, post square, story

### YouTube
- [ ] Canale YouTube "Il Tutor Digitale" creato
- [ ] Canale verificato con numero di telefono
- [ ] Foto profilo caricata (800×800px)
- [ ] Banner canale caricato (2560×1440px)
- [ ] Trailer canale creato e caricato (60 sec — chi sono + cosa trovi)
- [ ] Sezione "Informazioni" compilata al 100% (usa bio da `04-AGENTI-AI.md`)
- [ ] Sezioni playlist create (Smartphone, PC, Sicurezza, WhatsApp)
- [ ] Dati AdSense inseriti (anche se non ancora idonea)
- [ ] Primo video caricato (con thumbnail personalizzata)

### Facebook
- [ ] Pagina Facebook "Il Tutor Digitale" creata (categoria: Creator di contenuti)
- [ ] Foto profilo caricata
- [ ] Copertina caricata (820×312px)
- [ ] Sezione "Informazioni" compilata (usa bio da `04-AGENTI-AI.md`)
- [ ] Modalità Professionale attivata sul profilo personale
- [ ] Gruppo community "Il Tutor Digitale — Community" creato
- [ ] Gruppo collegato alla Pagina
- [ ] Dashboard Monetizzazione aperta (dati bancari inseriti)
- [ ] 3 post pubblicati prima del lancio (per non sembrare vuota)

### Instagram
- [ ] Account Creator creato (`@iltutordigitale`)
- [ ] Bio inserita (usa bio da `04-AGENTI-AI.md`)
- [ ] Foto profilo caricata
- [ ] Link Linktree inserito in bio
- [ ] Account collegato alla Pagina Facebook (da Meta Business Suite)
- [ ] 5 Highlight categories create (📱 💻 🔒 ❓ 🎓)
- [ ] Almeno 3 post/Reel pubblicati prima del lancio

### TikTok
- [ ] Account Creator creato (`@iltutordigitale`)
- [ ] Account Pro attivato
- [ ] Bio inserita (usa bio da `04-AGENTI-AI.md`)
- [ ] Link YouTube inserito in bio
- [ ] Foto profilo caricata

### Linktree
- [ ] Account Linktree creato (linktr.ee)
- [ ] Link configurati: YouTube, Facebook, Instagram, TikTok, sito web
- [ ] Colori Linktree: blu brand
- [ ] URL Linktree inserito nelle bio Instagram e TikTok

---

## FASE 2 — Portale web (Settimana 2-4)

### Struttura base
- [ ] Layout base (`BaseLayout.astro`) con Header e Footer
- [ ] Header responsive con navigazione mobile
- [ ] Footer con social links e newsletter mini
- [ ] Homepage (`index.astro`) con tutte le sezioni
- [ ] Pagina Chi sono (`/chi-sono`)
- [ ] Pagina Contatti (`/contatti`) con form funzionante
- [ ] Pagina Tutorial (`/tutorial`) con griglia video
- [ ] Pagina Prodotti (`/prodotti`) con affiliate

### Blog / SEO
- [ ] Sezione blog configurata (`/blog`)
- [ ] Schema contenuti (`config.ts`) creato
- [ ] Almeno 3 articoli blog pubblicati
- [ ] Sitemap XML configurata e funzionante
- [ ] Feed RSS configurato
- [ ] Meta tag SEO su tutte le pagine
- [ ] Open Graph configurato (immagine og-image.jpg creata)

### Funzionalità
- [ ] Form contatti funzionante (invia email)
- [ ] Newsletter form collegato a Brevo
- [ ] Lead magnet (guida PDF gratuita) pronto e scaricabile
- [ ] Cookie banner installato (Cookieyes o Iubenda)
- [ ] Privacy Policy pubblicata
- [ ] Google Search Console configurato
- [ ] Sitemap inviata a Google Search Console

### Performance
- [ ] Lighthouse Performance > 90
- [ ] Lighthouse SEO = 100
- [ ] Lighthouse Accessibility > 95
- [ ] Immagini ottimizzate (formato WebP dove possibile)
- [ ] Font con `font-display: swap`

---

## FASE 3 — Monetizzazione (Mese 2-3)

- [ ] Amazon Affiliati: account creato e approvato
- [ ] Almeno 5 prodotti affiliate inseriti nel portale
- [ ] Link affiliate nei video YouTube (descrizione)
- [ ] Prima guida PDF creata e caricata su Gumroad
- [ ] Gumroad account configurato con IBAN italiano
- [ ] Template email sponsorizzazione pronto (vedi Agente MoneyMax)
- [ ] Media Kit PDF creato

---

## FASE 4 — Go-live (fine Mese 1)

- [ ] Dominio custom live su Cloudflare Pages ✓ HTTPS
- [ ] Tutti i canali social attivi con contenuti
- [ ] Almeno 4 video YouTube pubblicati
- [ ] Almeno 8 post/Reel su Facebook e Instagram
- [ ] Portale web live e indicizzato da Google
- [ ] Primo articolo blog indicizzato
- [ ] Newsletter attiva con almeno 1 email di benvenuto automatica

### Test finale pre-lancio
- [ ] Sito testato su iPhone (Safari)
- [ ] Sito testato su Android (Chrome)
- [ ] Sito testato su PC (Chrome, Firefox)
- [ ] Tutti i link funzionanti (nessun 404)
- [ ] Form contatti testato
- [ ] Deploy automatico testato (push → live in 60 sec)
- [ ] Email `info@iltutordigitale.it` riceve messaggi

---

## Promemoria mensile (dopo il lancio)

Ogni mese:
- [ ] Piano editoriale del mese prossimo (Agente ContentCalendar)
- [ ] 4 video YouTube pubblicati
- [ ] Analytics review (YouTube Studio + Cloudflare Analytics + Search Console)
- [ ] Risposta a tutti i commenti in sospeso
- [ ] Aggiornamento prodotti affiliate (prezzi, disponibilità)
- [ ] 1 articolo blog nuovo
- [ ] Backup repository GitHub (automatico, ma verifica)
