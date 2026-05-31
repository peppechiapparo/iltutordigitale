# 11 — GDPR, Legale e Fisco

> Documento nuovo (assente nella bozza). Aspetti italiani obbligatori per un progetto che monetizza.
> ⚠️ Non è consulenza legale/fiscale: prima di emettere fatture o incassare, validare con un
> **commercialista**. Qui le regole pratiche che il progetto deve rispettare.

---

## 1. GDPR / Privacy

### Cosa serve sul portale
- **Privacy Policy** completa (finalità, basi giuridiche, dati raccolti, diritti dell'utente,
  responsabile del trattamento). Generabile con Iubenda (piano base gratuito) o equivalente.
- **Cookie Policy** + **cookie banner** se usi cookie/analytics di terze parti.
  - ✅ **Cloudflare Web Analytics è privacy-first (no cookie)** → con quello + nessun altro tracker,
    il banner non è necessario.
  - ❌ Se aggiungi Google Analytics/Meta Pixel → banner con consenso esplicito obbligatorio.
- **Form contatti e newsletter**: checkbox di consenso **non pre-spuntata** + link alla privacy.

### Newsletter (Brevo) — double opt-in
- **Double opt-in obbligatorio**: l'utente conferma l'iscrizione via email prima di ricevere invii.
- Conservare prova del consenso (data, IP) — Brevo lo gestisce.
- Ogni email deve avere link di **disiscrizione** funzionante.
- Lead magnet: la "Guida gratuita" si consegna **dopo** la conferma double opt-in.

### Dati raccolti — minimizzazione
Raccogliere solo il necessario (email per newsletter; nome+email+messaggio per contatti).
Niente profilazione non dichiarata.

---

## 2. Disclosure affiliate e contenuti sponsorizzati

Obbligo di trasparenza (AGCM / normativa consumatori + policy piattaforme):
- **Affiliate Amazon**: frase obbligatoria dove ci sono link, es.
  *"In qualità di Affiliato Amazon ricevo un guadagno dagli acquisti idonei."*
- **Contenuti sponsorizzati**: indicare chiaramente `#adv` / "in collaborazione con" su social e video.
- **Recensioni**: dichiarare se il prodotto è stato ricevuto gratuitamente.

---

## 3. Fisco (Italia)

> Necessario **prima** di incassare in modo continuativo (sponsor, prodotti, consulenze, AdSense).

- **Attività occasionale** (ricavi sporadici e non organizzati): possibile gestione con ritenuta
  d'acconto / prestazione occasionale entro limiti — **verificare soglie con commercialista**.
- **Attività continuativa** → **P.IVA**. Per molti creator il **regime forfettario** (con codice
  ATECO adeguato, es. servizi di informazione/produzione contenuti/pubblicità) è il punto di partenza
  più comune per i bassi volumi: imposta sostitutiva agevolata, contabilità semplificata.
- **AdSense / YouTube**: Google richiede dati fiscali; i pagamenti vanno dichiarati.
- **Fatturazione elettronica** verso aziende/sponsor italiane.
- **P.IVA in footer** del sito quando attiva (requisito già previsto in `05`).

### Checklist fiscale (con commercialista)
- [ ] Valutare attività occasionale vs P.IVA in base ai ricavi attesi
- [ ] Scegliere codice ATECO e regime (forfettario?)
- [ ] Configurare fatturazione elettronica
- [ ] Inserire dati fiscali su YouTube/AdSense, Gumroad, Amazon Affiliati
- [ ] Inserire P.IVA nel footer del portale

---

## 4. Marchio e nome

- Verificare che **"Il Tutor Digitale"** e l'handle social siano disponibili e non confliggano con
  marchi registrati (ricerca UIBM/EUIPO consigliata prima di investire nel brand).
- Valutare registrazione del marchio se il progetto cresce.

---

## 5. Minori e contenuti

- Il pubblico è adulto; se in futuro si trattano temi che coinvolgono minori (es. controllo
  parentale), nessun dato di minori va raccolto.

---

## 6. Sicurezza dei dati (dal KNOW_HOW)

- Segreti solo in `.env`/secret store, mai nel codice o nei log.
- Form con validazione e rate limiting (anti-spam/abuso).
- HTTPS ovunque (automatico Cloudflare).
- (Fase 2 engine) audit log di ogni approvazione human-in-the-loop; rotazione token API.
