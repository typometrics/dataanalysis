# TODO — Refactor `html_analyses/` site (UDW26 paper alignment)

Reference paper:
> Pegah Faghiri, Kim Gerdes, Sylvain Kahane (2026). *Verifying the Menzerath-Altmann law in the verbal domain in 180 languages.* UDW26 @ LREC 2026.

Replace the current site (per-language `mal_n_analysis*.html` reports) with a 3-tier structure that mirrors the paper.

---

## 1. Conventions to apply everywhere

### 1.1 β convention
- **Drop β(2→max).** Use **β(1→max)** as the canonical MAL effect score in all visible tables, plots and labels.
- Keep β(1→2) and β(2→max) only in the comparison scatter plots that explicitly need both.
- All instances of "β(2→max)" / "−β(2→max)" in titles, axis labels, tooltips, world-map legend, family bars, IE/VO bars must become "β(1→max)" / "−β(1→max)".
- Family/IE/VO bar charts and the world map currently use `start_n=2` → switch to `start_n=1`.

### 1.2 MAL effect labels (replace everywhere)
| current | new |
|---|---|
| β > 0.1 (green): MAL compliance | **MAL** |
| β < −0.1 (red): Anti-MAL | **Anti-MAL** |
| \|β\| ≤ 0.1 (yellow): Weak effect | **gray zone** |

Colors stay the same (green/red/yellow). Only the legend text changes.

### 1.3 MAL compliance (decrease ratio) labels + thresholds + colors
- Rename "decrease ratio" → **MAL compliance** everywhere (column header, tooltip, explanation text).
- New thresholds:
  - ratio ≥ 0.67 → **high**
  - 0.33 < ratio < 0.67 → **middle**
  - ratio ≤ 0.33 → **low**
- **Remove background colors** from MAL compliance cells (no green/yellow/red).

### 1.4 Regression mini-plots in tables (clickable SVGs)
- Use a **global fixed scale** shared by every language mini-plot in the site (computed once: x = log(1)..log(global_max_n); y = pooled log-MAL min/max with small margin). This makes slopes visually comparable.
- **Always render the full x-range** even when MAL_1 is excluded for low count (so n=1 position is reserved on every plot).
- Tick labels show n values (1, 2, 3, …, max) instead of log(n) values, paper-style.
- Mini-plots for the table column "MAL β(1→max)" must use `start_n=1`.

### 1.5 Regression popup (large modal chart)
- Same axis convention: fixed global scale, n-labels (1,2,3,…), x always covers n=1..max.
- Title shows MAL / Left MAL / Right MAL appropriately.

---

## 2. Site map (target)

```
html_analyses/
├── index.html                       # landing: paper ref + 3 links
├── mal_effect.html                  # main MAL effect page
│   ├── mal_effect_mal.html          # "more on MAL effect"
│   ├── mal_effect_lmal.html         # "more on LMAL effect"
│   └── mal_effect_rmal.html         # "more on RMAL effect"
├── mal_compliance.html              # MAL compliance index
│   ├── mal_compliance_summary.html  # summary table + comparison plots
│   ├── mal_compliance_mal.html      # full MAL_n table + per-direction plots
│   ├── mal_compliance_lmal.html
│   └── mal_compliance_rmal.html
├── mal_notebook_plots_and_commentary.html   # KEEP unchanged
└── UD_maps.html                     # KEEP unchanged
```

Files to **delete**:
- `mal_n_analysis.html`
- `mal_n_analysis_vo_languages.html`
- `mal_n_analysis_ov_languages.html`
- `mal_n_analysis_mixed_languages.html`
- `mal_analysis_report.html` (legacy)

---

## 3. Page-by-page content

### 3.1 `index.html`
- Header: paper title + author list + venue, with a citation block.
- One-sentence framing: "This site is the complete data presentation of the paper."
- **Three links (cards)** with short descriptions:
  1. **MAL Effect** → `mal_effect.html` — log-log regression slopes β(1→max) for MAL/LMAL/RMAL.
  2. **MAL Compliance** → `mal_compliance.html` — local change scores β(n→n+1) and decrease ratios.
  3. **Notebook Plots & Commentary** → `mal_notebook_plots_and_commentary.html`.
- (Optional secondary link: UD_maps.html.)

### 3.2 `mal_effect.html`
**Single big sortable table.** Columns:
| Language | Family | VO ratio | MAL β(1→max) (clickable mini-plot) | LMAL β(1→max) (clickable) | RMAL β(1→max) (clickable) |

Then **plots** in this order:
1. MAL vs LMAL scatter
2. MAL vs RMAL scatter
3. LMAL vs RMAL scatter
   *(unchanged from current `_generate_directional_scatter_section`, but use β(1→max), not β(2→max))*
4. **NEW**: Histogram of β(1→max) across languages, three overlaid semi-transparent series for MAL / LMAL / RMAL.
5. (Stretch goal — only if 4 is readable) same histogram split:
   - VO vs OV vs NDO
   - IE vs non-IE

At the bottom, links:
- "→ more on MAL effect" → `mal_effect_mal.html`
- "→ more on LMAL effect" → `mal_effect_lmal.html`
- "→ more on RMAL effect" → `mal_effect_rmal.html`

### 3.3 `mal_effect_{mal,lmal,rmal}.html`
Each page contains the per-direction "more" plots, using β(1→max) computed on the appropriate MAL/LMAL/RMAL data:
1. **World map** of −β(1→max) (shown first)
2. R² goodness-of-fit distribution for β(1→max) regressions
3. β(1→2) vs β(2→max) scatter (unchanged)
4. β(1→max) vs β(2→max) scatter (rename current "−β(2→max) vs −β(1→max)" axes if needed)
5. MAL effect −β(1→max) by language family
6. MAL effect −β(1→max): IE vs non-IE
7. MAL effect −β(1→max): VO vs OV vs NDO

Top of page: back-link to `mal_effect.html`.

### 3.4 `mal_compliance.html`
Brief explainer + **four commented links**:
1. **Summary** → `mal_compliance_summary.html`
2. **MAL** (bilateral, total) → `mal_compliance_mal.html`
3. **LMAL** (left) → `mal_compliance_lmal.html`
4. **RMAL** (right) → `mal_compliance_rmal.html`

### 3.5 `mal_compliance_summary.html`
- Summary table: Language | Family | VO | MAL compliance | LMAL compliance | RMAL compliance.
  (Compliance shown as plain numeric cell, no color background.)
- "Comparing LMAL, MAL, and RMAL Effect by Transition" SVG box plot (unchanged).
- "Negated Mean Local Change Scores by Language Family × Transition" heatmap (unchanged).

### 3.6 `mal_compliance_{mal,lmal,rmal}.html`
Each page contains the **current full per-language table** (column already there) but:
- Add column "MAL compliance" (renamed from "Decrease ratio"); no color.
- The β column is now β(1→max), not β(2→max). Mini-plot uses `start_n=1` and the global scale.
- Column order: Language | Family | VO | MAL β(1→max) (clickable) | MAL compliance | MAL_1 | β(1→2) | MAL_2 | β(2→3) | MAL_3 | …

Below the table:
- Local Change Score Distribution (box plot) — **truncated to n=5** (i.e. transitions 1→2, 2→3, 3→4, 4→5; drop 5→6 and beyond).
- Slope Distribution Summary table.
- Data Availability by n.

---

## 4. Plots to REMOVE entirely (no longer generated anywhere)
- "Individual Normalized MAL Curves in Log-Log Space (MAL_n / MAL_2)"
- "Individual Language MAL_n Trajectories"
- "Histogram of All Local Change Scores" (the log-scale Y mess)
- "Left-Side Mean MAL Curve" (and the symmetric Right-side one in `_get_directional_charts_section`)

---

## 5. Code changes in `mal_html_report.py`

1. **Add helpers**
   - `compute_global_scale(*lang2MAL_dicts)` → returns `(x_min, x_max, y_min, y_max)` covering log(1)..log(max_n) on x and pooled log(MAL) on y.
   - Tick-helper: log-tick positions and integer-n labels.

2. **Refactor `generate_loglog_svg`**
   - Accept optional `fixed_bounds=(xmin,xmax,ymin,ymax)` — when set, use them instead of per-plot bounds.
   - Always render n=1 marker position even if filtered.
   - Embed n-tick labels (paper style) for the popup as well (handled in JS popup using `Math.exp` + tick array).

3. **Refactor `_build_table`**
   - New signature option `start_n=1` (was effectively 2 inside).
   - New column order; rename "Decrease ratio" → "MAL compliance"; no background coloring.
   - Pass `fixed_bounds` to `generate_loglog_svg`.

4. **Compliance category function**
   - `_compliance_category(ratio)` returning "high" / "middle" / "low" with thresholds 0.67/0.33.
   - Use everywhere instead of the old 0.7/0.3 + colors logic.

5. **New top-level builders** (replace `generate_mal_html_report` / `generate_directional_mal_html_report`)
   - `generate_index_html(output_dir, paper_meta)`
   - `generate_mal_effect_html(...)` — main page (table + 3 scatter plots + histogram).
   - `generate_more_effect_html(direction, ...)` for direction in {"mal","lmal","rmal"} — 7 plots.
   - `generate_mal_compliance_index_html(output_dir)`
   - `generate_mal_compliance_summary_html(...)`
   - `generate_mal_compliance_detail_html(direction, ...)` — full table + box plot (≤n=5) + slope summary + availability.

6. **Delete** the now-unused functions:
   - `generate_directional_mal_html_report`
   - `_get_directional_html_header`
   - `_get_directional_charts_section`
   - chart blocks for: normalized MAL log-log, individual trajectories, histogram of all local change scores.

7. **Update strings**
   - All "Anti-MAL" / "MAL compliance" / "gray zone" labels per §1.2 — rewrite legend texts in `_get_html_header_with_nav`, `_get_table_explanation`, `_generate_directional_beta_table`, `_generate_svg_combined_box_plot`, etc.

---

## 6. Notebook changes (`08_menzerath_altmann_analysis.ipynb`)
- Replace the current `generate_mal_html_report(...)` and the loop calling `generate_directional_mal_html_report(...)` for VO/OV/Mixed subsets with calls to the new builders:
  ```python
  mal_html_report.generate_index_html(...)
  mal_html_report.generate_mal_effect_html(...)
  for d in ("mal", "lmal", "rmal"):
      mal_html_report.generate_more_effect_html(d, ...)
  mal_html_report.generate_mal_compliance_index_html(...)
  mal_html_report.generate_mal_compliance_summary_html(...)
  for d in ("mal", "lmal", "rmal"):
      mal_html_report.generate_mal_compliance_detail_html(d, ...)
  ```
- Drop the VO/OV/Mixed subset loop.

---

## 7. Implementation phases (do in this order)

- [ ] **Phase A — core utilities + label sweep**: add `compute_global_scale`, `_compliance_category`, sweep label/threshold strings (§1.2, §1.3), switch β(2→max) → β(1→max) in family bars / IE / VO / world map / R² distribution.
- [ ] **Phase B — refactor mini-plot + popup**: `generate_loglog_svg` with `fixed_bounds` and n-axis labels; popup JS uses n labels + fixed scale.
- [ ] **Phase C — page builders**:
  - `generate_index_html`
  - `generate_mal_effect_html` (table + 3 scatter + new histogram)
  - `generate_more_effect_html(direction)` ×3
  - `generate_mal_compliance_index_html`
  - `generate_mal_compliance_summary_html`
  - `generate_mal_compliance_detail_html(direction)` ×3
- [ ] **Phase D — wire into notebook**: replace old calls; run the relevant cell to regenerate `html_analyses/`.
- [ ] **Phase E — cleanup**: delete unused functions in `mal_html_report.py`; delete old `mal_n_analysis*.html` files; smoke-test all links.
