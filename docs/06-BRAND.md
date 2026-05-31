# 06 — Brand

> Sintesi operativa; per i dettagli grafici completi vedi anche la bozza `tutor-digitale-docs/06-BRAND-ASSETS.md`.

## Identità

- **Nome**: Il Tutor Digitale
- **Tagline**: Tecnologia per tutti — senza paura
- **Tono**: caldo, paziente, incoraggiante; mai condiscendente né gergale
- **Creator**: _da validare_ (vedi `01-VISIONE-STRATEGIA.md`)

## Palette

| Ruolo | Nome | HEX |
|-------|------|-----|
| Primario | Blu Brand | `#185FA5` |
| | Blu Medio | `#378ADD` |
| | Blu Chiaro | `#E6F1FB` |
| Accento | Arancione Vivo | `#EF9F27` |
| | Arancione Scuro | `#BA7517` |
| | Arancione Chiaro | `#FAC775` |
| Neutri | Grigio Scuro (testo) | `#2C2C2A` |
| | Grigio Medio | `#888780` |
| | Sfondo Caldo | `#F1EFE8` |
| | Bianco | `#FFFFFF` |

> Regola: nessun colore fuori palette (no verde/viola/rosso) nelle grafiche ufficiali.

## Tipografia

| Font | Peso | Uso |
|------|------|-----|
| **Nunito** | Bold 700 | H1-H3, logo, CTA, thumbnail |
| **Inter** | Regular 400 / Medium 500 | corpo, sottotitoli, etichette |

Scala (mobile-first, accessibile): H1 32-48 / H2 26-36 / H3 20-24 / corpo 17 / secondario 15 /
caption 13. **Mai sotto 13px.**

## Logo

Concept: monitor/schermo con punto interrogativo arancione (il dubbio del principiante + calore).
Varianti: principale (sfondo bianco), negativo (sfondo blu), icona quadrata, icona cerchio, favicon.
Regole: stesso logo ovunque; solo su sfondo bianco o blu brand; non distorcere; watermark piccolo
in basso a destra nei video.

## Coerenza cross-piattaforma

Stesso nome handle, stessa foto profilo, stessa palette su YouTube/Facebook/Instagram/TikTok.
Verificare disponibilità handle `@iltutordigitale` (o varianti) su **tutte** le piattaforme prima
di pubblicare.

## Asset da produrre (Canva)

Logo (5 varianti) · thumbnail YouTube 1280×720 · post IG 1080×1080 · copertina FB 820×312 ·
story/cover 1080×1920 · banner YT 2560×1440 · template guida PDF A4 · og-image 1200×630.

> Per le specifiche dimensioni complete dei social e i prompt AI per le immagini, riusare la
> tabella in `tutor-digitale-docs/06-BRAND-ASSETS.md` (ancora valida).

## Collegamento al design system del portale

Il brand qui definito **deve** essere la fonte dei token Tailwind (`web/tailwind.config.mjs`, vedi `03`)
e del file `.github/copilot-instructions.md`. La skill `ui-ux-pro-max` va usata da `astro-developer`
prima di implementare qualsiasi componente UI.
