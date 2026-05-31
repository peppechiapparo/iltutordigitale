# 09 — Deploy Workflow

> VSCode → GitHub → Cloudflare Pages. Build dal sottoprogetto `web/`.
> Lezione dal `KNOW_HOW`: **documentare il deploy** e non confondere Worker con Pages.

## Flusso

```
VSCode (web/) → git push → GitHub (PR) → GitHub Actions (build+typecheck) → Cloudflare Pages
                                                                                ↓
                                                            https://<dominio> (live ~60s)
```

## Branch strategy

```
main        → produzione (solo merge da PR approvate)
develop     → staging
feature/*   → nuove funzionalità
fix/*       → bugfix
content/*   → solo contenuti (nuovo articolo/tutorial)
```
Regole: mai commit diretti su `main`; ogni feature = branch + PR; PR deve passare il build;
Cloudflare crea preview URL per ogni PR.

## GitHub Actions — `.github/workflows/deploy.yml`

```yaml
name: Build and Deploy to Cloudflare Pages
on:
  push: { branches: [main, develop] }
  pull_request: { branches: [main] }
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions: { contents: read, deployments: write, pull-requests: write }
    defaults: { run: { working-directory: web } }   # <- build dal sottoprogetto web/
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm', cache-dependency-path: web/package-lock.json }
      - run: npm ci
      - run: npm run typecheck          # astro check
      - run: npm run build
        env:
          PUBLIC_SITE_URL: ${{ secrets.PUBLIC_SITE_URL }}
          AMAZON_AFFILIATE_TAG: ${{ secrets.AMAZON_AFFILIATE_TAG }}
      - uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: il-tutor-digitale
          directory: web/dist
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}
```

## Secrets GitHub

| Secret | Origine |
|--------|---------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare → My Profile → API Tokens |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare → Overview → Account ID |
| `AMAZON_AFFILIATE_TAG` | affiliate-program.amazon.it |
| `PUBLIC_SITE_URL` | `https://<dominio>` |

## package.json (web/) — script

```json
{ "scripts": {
  "dev": "astro dev", "build": "astro build", "preview": "astro preview",
  "typecheck": "astro check", "lint": "eslint src --ext .ts,.astro",
  "format": "prettier --write src/", "clean": "rm -rf dist .astro"
}}
```

## Cloudflare Pages — config build

```
Root directory:    web
Build command:     npm run build
Build output dir:  web/dist  (o "dist" se Root = web)
Node version:      20 (env NODE_VERSION = 20)
```

## Verifica post-deploy

```bash
curl -s https://tutordigitale.com/ | grep -E "(canonical|description)" | head -3
```

## Errori da NON ripetere (dal KNOW_HOW)

| Errore | Soluzione |
|--------|-----------|
| Confondere Worker e Pages | Il sito è **Pages** (integrazione Git); i Worker sono servizi separati |
| Modificare file in `dist/` | `dist/` è generato; modifica solo il sorgente in `web/src/` |
| Push senza verifica build | La PR deve passare GitHub Actions prima del merge |
| Secret nel codice | Solo `.env.local` (locale) e Secrets (GitHub/Cloudflare) |
| Token Cloudflare scaduto | Rigenerare token API |

## Email e dominio

- Dominio: **`tutordigitale.com`** registrato su **Cloudflare** (Registrar) → custom domain su Pages automatico.
- Credenziali CI/CD (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`): riuso dell'account Cloudflare
  già usato per il progetto scuolacipriani — da inserire come **GitHub Secrets** (mai nel codice).
- Cloudflare Email Routing: `info@tutordigitale.com` → casella personale (gratuito).
- Sitemap: Astro genera `sitemap-index.xml`; inviarla a Google Search Console.
