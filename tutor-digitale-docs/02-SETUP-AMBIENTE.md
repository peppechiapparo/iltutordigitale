# 02 — Setup Ambiente di Sviluppo

## Prerequisiti da installare

```bash
# 1. Node.js (versione LTS) — scarica da nodejs.org
node --version  # deve mostrare v20.x o superiore

# 2. Git — scarica da git-scm.com
git --version

# 3. VSCode — scarica da code.visualstudio.com

# 4. Wrangler CLI (Cloudflare)
npm install -g wrangler
wrangler --version
```

---

## Estensioni VSCode obbligatorie

Installa queste estensioni da VSCode (Ctrl+Shift+X):

```
astro-build.astro-vscode          ← Astro (syntax, IntelliSense)
bradlc.vscode-tailwindcss          ← Tailwind CSS IntelliSense
GitHub.copilot                     ← GitHub Copilot autocomplete
GitHub.copilot-chat                ← GitHub Copilot Chat (agente AI)
eamodio.gitlens                    ← GitLens (storia git avanzata)
esbenp.prettier-vscode             ← Prettier (formattazione automatica)
dbaeumer.vscode-eslint             ← ESLint (qualità codice)
ms-vscode.vscode-json              ← JSON support migliorato
formulahendry.auto-rename-tag      ← rinomina tag HTML automaticamente
```

### Estensioni opzionali utili
```
christian-kohler.path-intellisense ← autocomplete percorsi file
PKief.material-icon-theme          ← icone file nel pannello
```

---

## Configurazione VSCode (settings.json)

Premi `Ctrl+Shift+P` → "Open User Settings JSON" e aggiungi:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.tabSize": 2,
  "editor.wordWrap": "on",
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "github.copilot.enable": {
    "*": true
  },
  "tailwindCSS.experimental.classRegex": [
    ["clsx\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ],
  "astro.language-server.ls-path": ""
}
```

---

## Configurazione GitHub Copilot Pro

### Attivare Copilot Chat come agente di sviluppo

In VSCode, apri la chat Copilot (icona chat nella sidebar sinistra o `Ctrl+Shift+I`).

**Modalità agente**: clicca sul menu a tendina in alto nella chat e seleziona **"Agent"** (non "Ask" o "Edit").

In modalità Agent, Copilot può:
- Leggere e modificare file del progetto
- Eseguire comandi nel terminale
- Creare nuovi file
- Fare refactoring su più file contemporaneamente

### Istruzioni di sistema per Copilot (`.github/copilot-instructions.md`)

Crea questo file nel repo — Copilot lo legge automaticamente come contesto:

```markdown
# Copilot Instructions — Il Tutor Digitale

## Progetto
Portale web per il canale "Il Tutor Digitale" — tutorial tecnologia per principianti italiani.

## Stack
- Astro 4.x (SSG)
- Tailwind CSS 3.x
- TypeScript
- Cloudflare Pages (hosting)

## Convenzioni codice
- Componenti Astro in PascalCase: `VideoCard.astro`
- File utility in camelCase: `formatDate.ts`
- Costanti in UPPER_SNAKE_CASE
- Commenti in italiano
- Sempre TypeScript, mai JavaScript puro

## Brand
- Colore primario: #185FA5
- Colore accento: #EF9F27
- Font: Nunito (titoli), Inter (corpo testo)
- Tono: caldo, accessibile, mai tecnico

## Pubblico target
Italiani over 45, poca esperienza digitale. 
UI deve essere: testo grande, contrasto alto, navigazione semplice.

## Non fare mai
- Componenti con logica complessa nel template .astro
- CSS inline (usa solo classi Tailwind)
- Fetch senza error handling
- Commit di file .env o chiavi API
```

---

## Creazione repository GitHub

```bash
# 1. Vai su github.com → New Repository
# Nome: il-tutor-digitale
# Visibilità: Private (diventa Public solo a lancio)
# Inizializza con README: NO (lo creiamo noi)

# 2. Nel terminale VSCode:
cd ~/Desktop
mkdir il-tutor-digitale
cd il-tutor-digitale
git init
git remote add origin https://github.com/TUO-USERNAME/il-tutor-digitale.git
```

---

## Creazione progetto Astro

```bash
# Nella cartella del progetto:
npm create astro@latest . -- --template minimal --typescript strict --install --git

# Installa dipendenze aggiuntive:
npm install -D tailwindcss @astrojs/tailwind
npm install -D @astrojs/sitemap @astrojs/rss
npm install @astrojs/react react react-dom
npm install -D @types/react

# Configura Tailwind:
npx astro add tailwind
```

---

## Collegamento Cloudflare Pages

### Passo 1 — Cloudflare account
1. Registrati su cloudflare.com (gratuito)
2. Aggiungi il tuo sito (dominio)
3. Configura i nameserver come indicato in `01-ARCHITETTURA.md`

### Passo 2 — Cloudflare Pages
1. Dashboard Cloudflare → **Pages** → **Create a project**
2. **Connect to Git** → autorizza GitHub → seleziona `il-tutor-digitale`
3. Build settings:
   ```
   Framework preset:  Astro
   Build command:     npm run build
   Build output dir:  dist
   Node version:      20
   ```
4. **Save and Deploy** → primo deploy automatico

### Passo 3 — Dominio custom
1. Pages → tuo progetto → **Custom domains** → Add custom domain
2. Inserisci `iltutordigitale.it` (o il tuo dominio)
3. Cloudflare configura DNS automaticamente se il dominio è su Cloudflare Registrar

---

## GitHub Actions — Deploy automatico

Crea `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloudflare Pages

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      deployments: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          AMAZON_AFFILIATE_TAG: ${{ secrets.AMAZON_AFFILIATE_TAG }}

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: il-tutor-digitale
          directory: dist
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}
```

### Aggiungere i secrets su GitHub
1. Repository → Settings → Secrets and variables → Actions
2. Aggiungi:
   - `CLOUDFLARE_API_TOKEN` (da Cloudflare → My Profile → API Tokens)
   - `CLOUDFLARE_ACCOUNT_ID` (da Cloudflare → Overview → Account ID)
   - `ANTHROPIC_API_KEY`
   - `AMAZON_AFFILIATE_TAG`

---

## Workflow di sviluppo quotidiano

```bash
# Avvia server locale
npm run dev
# → apri http://localhost:4321

# Crea nuovo branch per ogni feature
git checkout -b feature/nuova-pagina-video

# Sviluppa con Copilot Agent attivo in VSCode

# Commit e push
git add .
git commit -m "feat: aggiungi pagina video tutorial"
git push origin feature/nuova-pagina-video

# Crea Pull Request su GitHub
# → Cloudflare Pages crea automaticamente un preview URL
# → Verifica il preview, poi fai merge su main
# → Deploy automatico in produzione
```

---

## Variabili d'ambiente locale

Crea `.env.local` nella root del progetto (NON committare):

```env
ANTHROPIC_API_KEY=sk-ant-inserisci-la-tua-chiave
AMAZON_AFFILIATE_TAG=iltutordigit-21
YOUTUBE_CHANNEL_ID=inserisci-id-canale
PUBLIC_SITE_URL=https://iltutordigitale.it
```

Aggiungi al `.gitignore`:
```
.env
.env.local
.env.production
node_modules/
dist/
.DS_Store
```
