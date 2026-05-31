---
name: bencium-impact-designer
description: Create distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Use when building or revising UI components, pages, or layouts. Based on Anthropic's Frontend Designer Skill by bencium.
version: 1.2.0
---

# Impact Designer — Principi per Il Tutor Digitale

Skill adattata per lo stack Astro 5 + Tailwind 3. I token brand del progetto
(`brand-*`) sono VINCOLANTI e sovrascrivono i suggerimenti generici sui colori.

## Principi fondamentali

### Gerarchia visiva forte
- Dimensioni tipografiche con rapporto matematico (1.25x o 1.333x tra livelli)
- Contrasto netto tra headline (Nunito Bold, grande) e corpo (Inter, leggibile)
- Spazio bianco generoso — non temere il vuoto
- Un unico elemento "eroe" per pagina cattura l'attenzione

### Layout non banale
- Asimmetria intenzionale: non tutte le sezioni devono essere centrate
- Sfondi con texture leggera o gradienti sottili (non piatti)
- Sezioni alternate: sfondo bianco / sfondo `brand-bg` (#F1EFE8) / sfondo `brand-blue`
- Card con accent strip colorato (bordo superiore brand-orange)

### Componenti con personalità
- Bottoni CTA: grandi (min-h-[52px]), arrotondati, con ombra leggera e hover animato
- Card hover: `translateY(-4px)` + `shadow-lg` + transizione 200ms
- Badge/pill per categorie: colori vivaci su sfondo tenue
- Icone SVG invece di emoji — più pulite e scalabili

### Anti-pattern da evitare (specifici per questo sito)
- ❌ Sfondo bianco piatto per tutte le sezioni senza variazione
- ❌ Card identiche senza accent visivo
- ❌ Testo grigio chiaro su sfondo chiaro (contrasto insufficiente)
- ❌ Sezioni hero troppo piccole — deve dominare la pagina
- ❌ CTA piccole o timide — over-45 ha bisogno di target grandi e chiari

### Specifico per pubblico over 45-65
- Font body MINIMO 17px (già nel sistema)
- Interlinea 1.7 (già nel sistema)
- Label esplicite su ogni azione — mai solo icone
- Pulsanti con testo descrittivo: "Inizia a leggere" non solo "→"
- Breadcrumb sempre visibile nelle pagine interne

## Hero section moderna
```
- Padding verticale: py-20 md:py-28
- H1: text-4xl md:text-5xl lg:text-6xl, tracking-tight
- Sottotitolo: text-xl md:text-2xl, max-w-2xl, opacity 80%
- Due CTA: primaria (brand-orange, grande) + secondaria (outline, trasparente)
- Sfondo: gradiente sottile da brand-blue-light a white
- Elemento decorativo: forma SVG o cerchio colorato in background (aria-hidden)
```

## Card tutorial moderna
```
- Border-top colorato (4px brand-orange) come accent
- Badge categoria in alto a sinistra
- Titolo con font-heading bold
- Snippet descrizione max 2 righe
- Footer card: data + "Leggi →" in brand-blue
- Hover: lift + ombra + titolo cambia in brand-blue
```

## Sezione categorie
```
- Grid 2 col mobile, 3 col tablet, 5 col desktop
- Ogni card: icona SVG colorata su sfondo brand-*
- Label grande + descrizione breve
- Hover: lift + ombra
```
