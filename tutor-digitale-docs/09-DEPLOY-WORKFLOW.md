# 09 — Deploy Workflow (VSCode → GitHub → Cloudflare Pages)

## Flusso completo

```
Sviluppo locale (VSCode)
        ↓ git push
GitHub Repository (branch feature/*)
        ↓ Pull Request → merge su main
GitHub Actions (build + test)
        ↓ build success
Cloudflare Pages (deploy automatico)
        ↓
https://iltutordigitale.it (live in ~60 secondi)
```

---

## Branch strategy

```
main          ← produzione (solo merge da PR approvate)
develop       ← staging / test integrazione  
feature/*     ← nuove funzionalità (es. feature/pagina-blog)
fix/*         ← bugfix (es. fix/menu-mobile)
content/*     ← solo aggiornamenti contenuti (es. content/nuovo-articolo)
```

### Regole
- **Mai committare direttamente su `main`**
- Ogni feature = branch separato = PR separata
- PR deve passare il build GitHub Actions prima del merge
- Cloudflare Pages crea un **preview URL** per ogni PR automaticamente

---

## File GitHub Actions completo

`.github/workflows/deploy.yml`:

```yaml
name: Build and Deploy to Cloudflare Pages

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      deployments: write
      pull-requests: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run typecheck
        # Aggiungi in package.json: "typecheck": "astro check"

      - name: Build
        run: npm run build
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          AMAZON_AFFILIATE_TAG: ${{ secrets.AMAZON_AFFILIATE_TAG }}
          PUBLIC_SITE_URL: ${{ secrets.PUBLIC_SITE_URL }}

      - name: Deploy to Cloudflare Pages
        id: deploy
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: il-tutor-digitale
          directory: dist
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}
          # branch: main → produzione | altri branch → preview

      - name: Comment PR with preview URL
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🚀 **Preview deploy pronto!**\n\nURL: ${{ steps.deploy.outputs.url }}'
            })
```

---

## Secrets da configurare su GitHub

Vai su: Repository → Settings → Secrets and variables → Actions → New repository secret

| Secret | Come ottenerlo |
|--------|---------------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare Dashboard → My Profile → API Tokens → Create Token → template "Edit Cloudflare Workers" |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Dashboard → Homepage → Account ID (lato destro) |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `AMAZON_AFFILIATE_TAG` | affiliate-program.amazon.it → Account → Il mio tag |
| `PUBLIC_SITE_URL` | `https://iltutordigitale.it` |

---

## Package.json — script utili

```json
{
  "scripts": {
    "dev":       "astro dev",
    "build":     "astro build",
    "preview":   "astro preview",
    "typecheck": "astro check",
    "lint":      "eslint src --ext .ts,.astro",
    "format":    "prettier --write src/",
    "clean":     "rm -rf dist .astro"
  }
}
```

---

## Workflow sviluppo quotidiano (step by step)

### Aggiungere un nuovo articolo blog

```bash
# 1. Crea branch
git checkout -b content/articolo-backup-android

# 2. Crea file Markdown
# src/content/blog/come-fare-backup-android.md

# 3. Scrivi contenuto (usa Agente SEOMax per ottimizzare)

# 4. Anteprima locale
npm run dev
# → http://localhost:4321/blog/come-fare-backup-android

# 5. Commit
git add .
git commit -m "content: aggiungi articolo backup Android"
git push origin content/articolo-backup-android

# 6. Apri PR su GitHub
# → Preview URL generato automaticamente da Cloudflare
# → Verifica preview
# → Merge su main → live automaticamente
```

### Aggiungere un nuovo componente

```bash
# 1. Crea branch
git checkout -b feature/componente-video-card

# 2. Sviluppa in VSCode con Copilot Agent
# Usa prompt: "Crea componente VideoCard.astro con le specifiche da 05-PORTALE-SPEC.md"

# 3. Test locale
npm run dev

# 4. Type check
npm run typecheck

# 5. Commit e PR
git add .
git commit -m "feat: aggiungi componente VideoCard"
git push origin feature/componente-video-card
```

---

## Cloudflare Pages — configurazione build

Nel pannello Cloudflare Pages → tuo progetto → Settings → Builds & deployments:

```
Build command:           npm run build
Build output directory:  dist
Root directory:          / (lascia vuoto)
Node.js version:         20 (in Environment variables: NODE_VERSION = 20)
```

### Environment Variables su Cloudflare Pages
Settings → Environment variables → Add variable (per Production e Preview):

```
ANTHROPIC_API_KEY     = sk-ant-...
AMAZON_AFFILIATE_TAG  = iltutordigit-21
PUBLIC_SITE_URL       = https://iltutordigitale.it
NODE_VERSION          = 20
```

---

## Cloudflare Email Routing (gratuito)

Crea `info@iltutordigitale.it` senza acquistare un server email:

1. Cloudflare Dashboard → Email → Email Routing → Enable
2. Add address: `info@iltutordigitale.it`
3. Forward to: la tua email Gmail/personale
4. Tutte le email a `info@iltutordigitale.it` arrivano nella tua casella personale

---

## Monitoring e analytics

| Tool | Costo | Cosa monitora |
|------|-------|---------------|
| Cloudflare Web Analytics | Gratuito | Visite, pagine viste, paese, device |
| Google Search Console | Gratuito | Posizioni SEO, click, impressioni |
| Cloudflare Speed | Gratuito | Performance globale |
| GitHub Actions logs | Gratuito | Status deploy, errori build |

### Aggiungere Google Search Console
1. Vai su search.google.com/search-console
2. Aggiungi proprietà → inserisci dominio
3. Verifica con record TXT su Cloudflare DNS
4. Invia sitemap: `https://iltutordigitale.it/sitemap-index.xml` (generata da Astro automaticamente)
