# Poster V4 — Todo List

V3 preserved as `poster_v3.tex` / `poster_v3.pdf`.

---

## Analysis of Co-Author Feedback

### Sources
- **Co-author 1 (Sylvain Kahane)**: 3 items, ordered by importance
- **Co-author 2**: Multiple items on charts, legends, text corrections, and optional additions (IE vs non-IE, world map)

---

## Contradictions, Ambiguities & Questions

### 1. Strip plots vs. bar charts — which format?
Co-author 2 refers to "Barcharts" and mentions modifying legends, removing means, and adding vertical threshold lines. But V3 **already replaced bar charts with strip/beeswarm plots** (extracted from the website). These strip plots:
- Already show individual language dots (no "mean" to remove)
- Already have an IQR box (not a "mean")
- Don't have MAL/Anti-MAL colored bars

**Question:** Are co-author 2's comments about the _old V2 bar charts_ that were already removed? Should we:
- (a) Modify the **current strip plots** to match the spirit of these requests (change legend, add threshold lines, reorder, recolor)?
- (b) Go **back to bar charts** but with the requested modifications?
- (c) **Generate new strip plots from scratch** with the correct order, colors, and threshold lines?

**Recommendation:** Option (c) — regenerate strip plots from scratch with all requested changes baked in, since the current ones are extracted from website HTML and hard to modify.

### 2. Color conflicts
Co-author 2 says:
- Use `green = MAL (β > 0.1)` and `red = Anti-MAL (β < -0.1)` for threshold lines/legends
- But then: _"changer la palette des couleurs (car on a utilisé le vert et le rouge pour MAL et Anti-MAL)"_ — change OV/NDO/VO palette to avoid green and red since those are used for MAL/Anti-MAL

Currently in the strip plots:
- VO = `#2196F3` (blue), OV = `#4CAF50` (green), NDO = `#F44336` (red)

So green (OV) and red (NDO) clash with the MAL/Anti-MAL semantic colors. Need a new OV/NDO/VO palette that avoids green and red.

**Proposed new palette:** blue / orange / purple (or similar warm-neutral triad).

### 3. World map vs IE comparison — placement conflict
Co-author 2 says: _"La carte du monde ou la comparaison IE vs. Non-IE qui peut facilement aller en haut à droite dans l'espace qui reste après la définition."_

But the current V3 layout has **two equal-width columns** in Section 1, and the right column ("Left vs. right") is **already full** of text. There is no obvious "space that remains after the definition."

**Question:** Should we:
- (a) Make the right column layout 2 blocks (text + small chart below)?
- (b) Create a narrow 3rd column on the right for the chart?
- (c) Skip this addition if it doesn't fit?

Also: Should it be the IE vs non-IE comparison OR the world map? Co-author 2 seems to prefer IE vs non-IE, with the world map as a tiny optional extra.

### 4. World map legend inconsistency
Co-author 2 notes: _"corriger la légende: le titre dit B(1→max) et la légende dit B(2→Max) — a priori il nous faut B(1→max)"_

This is about the **website's** world map, not something currently on the poster. If we do add the world map, we'd generate it fresh with the correct β(1→max) label. Not an issue for the poster itself.

### 5. "MAL is stronger for VO" claim
Co-author 2 says this text is wrong: _"MAL is stronger for VO languages"_ — it's just a numerical difference that can't be generalized, and there is no paradox.

The current V3 text (line 247) says: "MAL is stronger for **VO languages** (56%) than OV (42%), but RMAL and LMAL are **stronger for OV**! Where does the paradox come from?"

**Replace with:** Something like "MAL and Anti-MAL types are fairly equally distributed in VO and OV languages" or "MAL is fairly impartial to word order."

### 6. QR code repositioning
Co-author 1 wants the QR code moved from the masthead to after "You?" in Section 2, with catchy text like "We know the truth about you". This means:
- Remove or shrink the QR block in the masthead
- Add QR + catchy text in the case studies section
- Remove the line "And you? Check your language at typometrics.elizia.net!" from Arabic text
- Make it clear that the QR links to a website (not just the poster/paper)

---

## Task List

### 0. Preserve V3
- [x] Copy `poster.tex` → `poster_v3.tex`
- [x] Copy `poster.pdf` → `poster_v3.pdf`

### 1. Strip plots: reorder, recolor, relabel (Co-author 1 item 1 + Co-author 2 barcharts items)

#### 1a. Homogenize order across all three plots
Current state:
- `poster_strip_mal.svg`: VO (top), OV, NDO (bottom) — **wrong order**
- `poster_strip_rmal.svg`: OV (top), NDO, VO (bottom) — **wrong order**
- `poster_strip_lmal.svg`: OV (top), NDO, VO (bottom) — **wrong order**

Target order (top→bottom): **OV < NDO < VO** (matching the other diagrams)

- [x] Regenerate all 3 strip plots with order: OV (top), NDO (middle), VO (bottom)

#### 1b. Homogenize colors
Current colors: VO=blue (#2196F3), OV=green (#4CAF50), NDO=red (#F44336)
Problem: green/red clash with MAL/Anti-MAL semantic coding

- [x] Choose new OV/NDO/VO palette that avoids green and red
- [x] Apply same palette consistently to all 3 plots

#### 1c. Fix legend text
Current: `−β(1→max) — positive = MAL compliance`
Target: `β > 0.1 = MAL` & `β < −0.1 = Anti-MAL`

- [x] Update x-axis label / legend in all 3 plots

#### 1d. Remove mean line, add threshold lines
- [x] Remove any mean/median vertical lines (the IQR box median line in strip plots)
- [x] Add vertical dashed lines at β = −0.1 and β = +0.1 (MAL/Anti-MAL thresholds)

#### 1e. Generate new PDFs
- [x] Convert updated SVGs → PDFs via cairosvg (or regenerate via matplotlib)

### 2. QR code repositioning (Co-author 1 items 2)

- [x] Remove QR code from masthead (or keep just URL text?)
- [x] Add QR code after "You?" in Section 2 (case studies), with catchy text
- [x] Use text: **"We know the truth about you"** (per final suggestion)
- [x] Remove line "And you? Check your language at typometrics.elizia.net!" from Arabic caption
- [x] Make it clear the QR goes to the interactive website

### 3. β threshold definition on new line (Co-author 1 item 3)

Current (line 189): `β > 0.1: MAL language. β < −0.1: Anti-MAL. In between: grey zone.` — all on same line as definition text.

- [x] Move "β > 0.1: **MAL language**. β < −0.1: **Anti-MAL**. In between: **grey zone**." to its own line/paragraph

### 4. Fix "MAL by word order" text (Co-author 2)

Current text: "MAL is stronger for **VO languages** (56%) than OV (42%), but RMAL and LMAL are **stronger for OV**! Where does the paradox come from?"

- [x] Replace with: "MAL is fairly impartial to word order: MAL and Anti-MAL types are fairly equally distributed in VO and OV languages."

### 5. (Optional) Add IE vs non-IE comparison or world map

> Depends on answer to Question 3 above (space availability).

- [ ] Decide: IE vs non-IE strip plot, or world map, or skip
- [ ] If IE vs non-IE: extract from `mal_effect_mal.html` (it exists), apply new color palette (different from OV/NDO/VO), fix legend
- [ ] If world map: generate small map, fix β(1→max) label
- [ ] Find placement: top-right area of Section 1, or squeeze into layout

### 6. Compilation & verification

- [x] Compile with lualatex (1 page, no errors)
- [ ] Visual check: all plots consistent in order and color
- [ ] Visual check: QR code legible and well-placed
- [ ] Visual check: threshold text on separate line
- [ ] Generate preview image
