# SKILL: tutor-digitale-design

## Descrizione

Design system di riferimento per il portale **Il Tutor Digitale**. Garantisce coerenza visiva e
**accessibilità reale** per un pubblico italiano over 45-65 principiante.

Attivare questa skill **ogni volta** che un agente deve:
- Creare o modificare componenti Astro / Tailwind
- Aggiungere una pagina al portale
- Decidere colori, tipografia, spacing, iconografia
- Revisionare lo stile di componenti esistenti

---

## Fonte di verità

Prima di scrivere qualsiasi CSS o componente, leggere:
```
docs/06-BRAND.md           ← palette, tipografia, logo, regole
docs/05-PORTALE-SPEC.md    ← specifiche componenti e accessibilità
```
I token Tailwind in `web/tailwind.config.mjs` derivano da `docs/06-BRAND.md`.

---

## Regole non negoziabili

### Palette (solo questi colori)
- Blu: `#185FA5` / `#378ADD` / `#E6F1FB`
- Arancione: `#EF9F27` / `#BA7517` / `#FAC775`
- Neutri: `#2C2C2A` (testo) / `#888780` / `#F1EFE8` (sfondo) / `#FFFFFF`
- **Vietato** introdurre colori fuori palette (verde/viola/rosso).

### Tipografia
- Titoli: **Nunito Bold** (`font-heading`). Corpo: **Inter** (`font-sans`).
- Corpo testo **17px** minimo; **mai sotto 13px**.

### Accessibilità (requisito, non opzionale)
- Contrasto WCAG **AA** minimo (4.5:1).
- `aria-label` su bottoni icona; `alt` descrittivo o `alt=""` se decorativa.
- `focus-visible` sempre visibile (3px outline arancione); mai rimuovere l'outline.
- Skip-link "Vai al contenuto"; navigazione completa da tastiera.
- Target touch ≥44px.

### Implementazione
- **Mobile-first**: progetta a 375px, poi desktop con breakpoint Tailwind.
- **Zero CSS inline**: solo classi Tailwind brand (`text-brand-blue`, `bg-brand-orange`, …).
- Componenti piccoli e riutilizzabili; logica complessa in file `.ts` separati.

---

## Anti-pattern (da evitare)

- Testo piccolo o grigio chiaro su sfondo chiaro (contrasto insufficiente).
- Menu/navigazione complessi: il pubblico ha bisogno di percorsi semplici e grandi.
- Animazioni che distraggono o riducono la leggibilità.
- Icone senza etichetta testuale per azioni importanti.
