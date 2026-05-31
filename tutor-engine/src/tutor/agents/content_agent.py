"""Content Agent — genera bozze di contenuto dal calendario editoriale approvato.

Pattern: Template Method + ReAct.
Formati supportati:
  - "YouTube lungo"  → script completo (10-14 min): hook, promessa, tutorial, recap, CTA
  - "YouTube Short"  → script breve (30-45s): hook, 1 trucco, CTA
  - "Reel IG + TikTok" / "Reel Facebook" → copy breve (45-60s)
  - "Post community Facebook" → testo conversazionale + domanda
  - "Articolo blog"  → articolo AEO-ready (H1, "In breve", passi, FAQ)

Gate umano: dopo la generazione invia su Telegram con ✅/✏️/❌.
"""

from __future__ import annotations

import json
from typing import Any

from ..core.db import Database
from ..core.logging import get_logger
from .base import LLMAgent, Finding

log = get_logger(__name__)

# ─── System prompt template ──────────────────────────────────────────────────

CONTENT_SYSTEM_PROMPT = """\
Sei il content creator de **Il Tutor Digitale** — portale di tutorial tecnologici
per italiani over 45-65 principianti. Creator: Giuseppe.

## Voce e tono
- Italiano colloquiale, caldo, rassicurante. MAI condiscendente.
- Zero gergo non spiegato. Se usi un termine tecnico, spiegalo subito con parole semplici.
- Parla come "una figlia/figlio che spiega con pazienza alla mamma/papà".
- Usa "tocca", "schermo", "telefono" — non "clicca", "display", "device".

## Pillar tematici
1. Smartphone — uso quotidiano (foto, app, impostazioni, spazio)
2. WhatsApp & messaggistica — videochiamate, gruppi, backup, aggiornamenti
3. Sicurezza online — truffe, password, SPID, phishing, SMS sospetti
4. PC & internet — email, navigazione, stampa, file, browser
5. App utili — banca, Fascicolo Sanitario, PagoPA, mappe, trasporti

## Il tuo compito
Genera il contenuto per: **{format}** — **{topic}**
Pillar: {pillar} | Keyword: {keywords}

{format_instructions}

Quando hai generato il contenuto, usa il tool `save_draft` per salvarlo.
NON pubblicare — produci solo la bozza.
"""

FORMAT_INSTRUCTIONS = {
    "YouTube lungo": """\
## Struttura script YouTube lungo (10-14 min)
1. **HOOK** (0-15s): domanda o scenario che il pubblico over-60 riconosce subito
2. **PROMESSA** (15-30s): "In questo video ti mostro passo per passo come..."
3. **CHI SONO** (30-45s, solo se primo video): breve presentazione Giuseppe
4. **TUTORIAL** (2-12 min): passi numerati, lenti, con note regia [mostra schermo], [zoom su tasto]
5. **RECAP** (1 min): riepilogo 3 punti chiave
6. **CTA** (30s): "Se ti è stato utile metti mi piace, iscriviti..."

Scrivi lo script completo con le battute esatte (non solo outline).
Include note regia tra [parentesi quadre] per ogni azione sullo schermo.
""",
    "YouTube Short": """\
## Struttura YouTube Short (30-45s)
1. **HOOK** (0-3s): domanda fulminea ("Sai come fare X in 30 secondi?")
2. **TRUCCO** (3-35s): 1 solo trucco, spiegato step-by-step
3. **CTA** (35-45s): "Per la guida completa, trovi tutto sul canale!"

Massimo 150 parole. Ogni frase = 1 step.
""",
    "Reel IG + TikTok": """\
## Struttura Reel (45-60s)
Questo Reel è tratto dal video YouTube della settimana sullo stesso argomento.
1. **HOOK** visivo (0-3s): testo grande sullo schermo + domanda
2. **PROBLEMA** (3-10s): "Quante volte ti è capitato..."
3. **SOLUZIONE** (10-45s): 3 step mostrati velocemente
4. **CTA** (45-60s): "Segui per altri consigli utili! Link in bio."

Scrivi: copy parlato + didascalie per ogni step + hashtag (10-15, mix italiano/generico).
""",
    "Reel Facebook": """\
## Struttura Reel Facebook (stesso del Reel IG)
Come il Reel IG/TikTok della settimana — adatta solo il testo CTA:
"Seguici per altri consigli! Trovi tutto sul gruppo..."
""",
    "Post community Facebook": """\
## Struttura Post community Facebook
Un post conversazionale che stimola la discussione nel gruppo.
1. **Apertura** (1-2 righe): situazione reale che il pubblico riconosce
2. **Domanda** (1 riga): domanda semplice e aperta
3. **Invito** (1 riga): "Scrivi nei commenti..."

Max 100 parole. Tono da "amico di famiglia". Includi 2-3 emoji di contesto.
""",
    "Articolo blog": """\
## Struttura Articolo Blog AEO-Ready (1200-1500 parole)
1. **H1** (= keyword principale, max 65 caratteri): risponde alla domanda dell'utente
2. **"In breve"** (box 40-60 parole): risposta sintetica alla domanda principale
3. **Introduzione** (100-150 parole): problema + empatia + cosa vedrà
4. **Contenuto** (H2/H3 + passi numerati): guida passo-passo dettagliata
5. **FAQ** (3-5 domande): le domande più frequenti, con risposta breve (2-4 righe)
6. **CTA finale**: link a video YouTube correlato + invito a commentare

Per i `faq_schema`, genera un array JSON con oggetti {"question": "...", "answer": "..."}.
""",
}


CONTENT_TOOLS = [
    {
        "name": "save_draft",
        "description": "Salva la bozza del contenuto generato nel database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content_type": {
                    "type": "string",
                    "enum": ["script_youtube", "script_short", "reel", "post_facebook", "article"],
                    "description": "Tipo di contenuto",
                },
                "title": {
                    "type": "string",
                    "description": "Titolo del contenuto (per script: titolo video; per articoli: H1)",
                },
                "body": {
                    "type": "string",
                    "description": "Testo completo del contenuto generato",
                },
                "seo_title": {
                    "type": "string",
                    "description": "Titolo SEO (max 65 caratteri) — solo per articoli blog",
                },
                "meta_desc": {
                    "type": "string",
                    "description": "Meta description (70-160 caratteri) — solo per articoli blog",
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keyword principali del contenuto",
                },
                "faq_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "answer":   {"type": "string"},
                        },
                    },
                    "description": "FAQ schema strutturato — solo per articoli blog",
                },
            },
            "required": ["content_type", "title", "body"],
        },
    }
]

# Mappa formato calendario → tipo di contenuto DB
FORMAT_TO_CONTENT_TYPE = {
    "YouTube lungo":      "script_youtube",
    "YouTube Short":      "script_short",
    "Reel IG + TikTok":  "reel",
    "Reel Facebook":      "reel",
    "Post community Facebook": "post_facebook",
    "Articolo blog":      "article",
}


class ContentAgent(LLMAgent):
    """Genera bozze di contenuto da una voce del calendario editoriale approvato.

    Accetta un `calendar_id` specifico oppure processa la prima voce approvata
    senza draft associato.
    """

    name = "content_agent"
    MAX_ITERATIONS = 8  # contenuto generativo, non serve loop lungo

    def __init__(self, db: Database, llm: Any, calendar_id: int | None = None) -> None:
        super().__init__(db, llm)
        self._calendar_id = calendar_id
        self._draft_result: dict | None = None
        self._current_calendar_id: int | None = None

    def collect(self) -> dict:
        """Recupera la voce del calendario da elaborare."""
        with self._db.connect() as conn:
            if self._calendar_id is not None:
                row = conn.execute(
                    "SELECT * FROM editorial_calendar WHERE id = ?",
                    (self._calendar_id,),
                ).fetchone()
            else:
                # Prima voce approvata senza draft
                row = conn.execute(
                    """SELECT ec.* FROM editorial_calendar ec
                       LEFT JOIN drafts d ON d.calendar_id = ec.id AND d.status != 'scartato'
                       WHERE ec.status = 'approvato' AND d.id IS NULL
                       ORDER BY ec.date ASC LIMIT 1""",
                ).fetchone()

        if row is None:
            return {"error": "Nessuna voce del calendario da elaborare."}

        self._current_calendar_id = row["id"]
        keywords = json.loads(row["keywords"] or "[]")

        return {
            "calendar_id": row["id"],
            "format": row["format"],
            "pillar": row["pillar"],
            "topic": row["topic"],
            "keywords": keywords,
            "date": row["date"],
        }

    def build_system_prompt(self, context: dict) -> str:
        if "error" in context:
            return "Rispondi solo: 'Nessun contenuto da generare.'"

        fmt = context.get("format", "Articolo blog")
        instructions = FORMAT_INSTRUCTIONS.get(
            fmt,
            FORMAT_INSTRUCTIONS["Articolo blog"]
        )

        return CONTENT_SYSTEM_PROMPT.format(
            format=fmt,
            topic=context.get("topic", ""),
            pillar=context.get("pillar", ""),
            keywords=", ".join(context.get("keywords", [])),
            format_instructions=instructions,
        )

    def get_tools(self) -> list[dict]:
        return CONTENT_TOOLS

    def _dispatch_tool(self, tool_name: str, tool_input: dict) -> str:
        """Gestisce save_draft (agent-specific)."""
        if tool_name != "save_draft":
            return super()._dispatch_tool(tool_name, tool_input)

        from datetime import datetime
        now = datetime.now().isoformat(timespec="seconds")

        with self._db.connect() as conn:
            conn.execute(
                """INSERT INTO drafts
                   (calendar_id, agent, content_type, title, body,
                    seo_title, meta_desc, keywords, faq_schema,
                    status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'bozza', ?)""",
                (
                    self._current_calendar_id,
                    self.name,
                    tool_input.get("content_type", "article"),
                    tool_input["title"],
                    tool_input["body"],
                    tool_input.get("seo_title"),
                    tool_input.get("meta_desc"),
                    json.dumps(tool_input.get("keywords", []), ensure_ascii=False),
                    json.dumps(tool_input.get("faq_schema", []), ensure_ascii=False),
                    now,
                ),
            )
            draft_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        self._draft_result = {
            "id": draft_id,
            "title": tool_input["title"],
            "content_type": tool_input.get("content_type"),
        }
        log.info("draft_saved", draft_id=draft_id, title=tool_input["title"])
        return json.dumps({"ok": True, "draft_id": draft_id})

    def _build_initial_message(self, context: dict) -> str:
        if "error" in context:
            return context["error"]
        fmt = context.get("format", "Articolo blog")
        kw = ", ".join(context.get("keywords", []))
        return (
            f"Genera il contenuto per il seguente slot del calendario:\n\n"
            f"- **Formato**: {fmt}\n"
            f"- **Argomento**: {context.get('topic', '')}\n"
            f"- **Pillar**: {context.get('pillar', '')}\n"
            f"- **Keyword**: {kw}\n"
            f"- **Data**: {context.get('date', '')}\n\n"
            f"Genera il contenuto completo e salvalo con `save_draft`."
        )

    def _build_summary(self, status: object, findings: object) -> str:
        if self._draft_result is None:
            return "Nessuna bozza generata."

        d = self._draft_result
        fmt_label = {
            "script_youtube": "Script YouTube",
            "script_short":   "YouTube Short",
            "reel":           "Reel",
            "post_facebook":  "Post Facebook",
            "article":        "Articolo Blog",
        }.get(d.get("content_type", ""), d.get("content_type", ""))

        return (
            f"✍️ *Bozza pronta — {fmt_label}*\n\n"
            f"📌 *{d['title']}*\n"
            f"🆔 Draft ID: {d['id']}\n\n"
            f"Revisiona e approva per procedere con la pubblicazione."
        )
