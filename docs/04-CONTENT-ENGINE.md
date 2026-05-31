# 04 — Content Engine Agentico (Fase 2, opzionale)

> Riuso diretto del blueprint `KNOW_HOW.md` (progetto Shan Growth Agent).
> **Da costruire solo quando il volume manuale diventa insostenibile** (anti-over-engineering).
> Tutto ciò che è automatizzabile deve comunque passare da un **gate umano** prima di agire nel mondo.

---

## Obiettivo

Automatizzare la parte ripetitiva della produzione contenuti — **senza** togliere il controllo
editoriale all'umano:

```
idea/tema → script (LLM) → ottimizzazione SEO/AEO (LLM) → bozza completa → [GATE UMANO] → pubblicazione
                                                                                ✅ / ✏️ / ❌
```

L'engine **non pubblica mai** in autonomia. Produce bozze; l'umano approva, modifica o scarta.

---

## Architettura (pattern dal KNOW_HOW)

### Template Method — `Agent.run()`
```
run() = collect() → analyze() → persist() → report
```
- `collect()` → solo I/O (es. legge metriche YouTube, temi pendenti)
- `analyze()` → trasforma in `(status, summary, findings)`
- persistenza, timing, logging, gestione errori → nella base class

### ReAct loop — `LLMAgent`
- `MAX_ITERATIONS = 15` (cap anti token-burn)
- sottoclassi implementano `build_system_prompt()` + `get_tools()`
- tool speciale `report_findings` termina il loop

### Strategy + Factory — provider LLM
| Client | Note |
|--------|------|
| `GitHubModelsClient` | **default per prototipi** (free tier, eredita da OpenAIClient) |
| `OpenAIClient` / `AnthropicClient` | quando il volume cresce (solo config, no refactor) |
| `NullLLMClient` | degradazione controllata se manca config |

### Tool layer (deterministico)
Capability come `schema JSON + funzione Python` in un `TOOL_DISPATCH`:
```python
TOOL_DISPATCH = {
  "fetch_youtube_metrics": tool_fetch_youtube_metrics,
  "fetch_search_console": tool_fetch_search_console,
  "extract_keywords": tool_extract_keywords,
  "build_faq_schema": tool_build_faq_schema,
  "save_draft": tool_save_draft,
}
```

### Gate umano — Notifier
Telegram bot in **polling** (nodo in LAN, no webhook) con `InlineKeyboardMarkup`:
`✅ Approva` / `✏️ Modifica` / `❌ Scarta`. Ogni decisione è loggata (audit).

---

## Agenti dell'engine

| Agente | collect() | analyze() (LLM) | Output |
|--------|-----------|------------------|--------|
| **ScriptAgent** | tema + format + dati performance | scrive script (regole `07`) | bozza script + titolo/thumbnail/keyword |
| **SeoAeoAgent** | bozza script + keyword | titoli, descrizioni, FAQ schema, hashtag | metadati ottimizzati SEO+AEO |
| **CalendarAgent** | metriche YT/GSC ultimi 30gg | propone temi/formati prossime 4 settimane | calendario editoriale |

> Loop analitico (direzione C del KNOW_HOW): `CalendarAgent` chiude il ciclo usando i dati reali
> di performance per decidere cosa produrre, invece di indovinare.

---

## Confine deterministico vs LLM

| Deterministico (funzioni/tool) | LLM (ragiona/orchestra) |
|--------------------------------|--------------------------|
| Fetch metriche API, parsing JSON | Scelta del tema in base ai trend |
| Generazione FAQ schema da campi | Scrittura dello script |
| Validazione lunghezza titolo (≤60) | Ottimizzazione copy SEO/AEO |
| Salvataggio bozza, audit log | Sintesi insight dai dati |

---

## Persistenza e deploy

- SQLite (WAL): tabelle `agent_runs` + `findings` + `drafts` + `approvals`.
- Docker `restart: unless-stopped`; deploy: package → scp → rebuild (vedi `09`).
- Nessun modello ML locale su hardware debole: usare API esterne.

---

## Quando NON costruire l'engine

- < ~8 contenuti/mese → la produzione manuale con gli **agenti VS Code** (`13`) è sufficiente.
- L'engine si giustifica quando: volume alto, più canali, necessità di ripetibilità e di chiudere
  il loop dati in modo sistematico.
