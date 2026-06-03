# Short Before Long (SBL) / Helix Analysis Presentation Plan

This document outlines the plan to present the SBL (Helix) workflow, tables, and results in a cohesive set of HTML pages, similar to the existing MAL analysis site (`mal_site.py`).

## 1. Current Scripts Involved in SBL Computation
The following scripts currently handle the extraction, computation, and legacy HTML generation for SBL / Helix analyses:

### Data Processing & Core Computations
- `verb_centered_analysis.py`: Main API and entry point for computing SBL/helix tables.
- `verb_centered_computations.py`: Core logic for calculating sizes, growth factors, and ordering statistics.
- `verb_centered_builder.py`: Constructs the hierarchical table structures.
- `verb_centered_layout.py`: Computes column and row layouts for the helix representation.
- `verb_centered_formatters.py`: Exports results to TSV, Text, or Excel.
- `conll_processing.py`: Extracts the raw position/size statistics from CONLLU treebanks.

### Legacy HTML Generation
- `generate_html_examples.py`: The older script that currently generates HTML outputs featuring Standard and "AnyOtherSide" Helix tables.

### Orchestration Notebooks
- `04_data_processing.ipynb`: Orchestrates the verb-centered analysis workflow.
- `05_comparative_visualization.ipynb`: Explores visualizations for these tables.

---

## 2. Proposed Site Structure
We propose creating a new generator script (e.g., `sbl_site.py`) that builds a standalone static site in a new directory `html_sbl_analyses/`, using the same modern aesthetic as `html_analyses/`.

- **`index.html` (Home)**
  - Introduction to the "Short Before Long" principle.
  - Explanation of Helix tables (Standard vs. AnyOtherSide) and underlying metrics.
- **`sbl_laws_explained.html` (The Sy Laws)**
  - **Explicit reformulation of the Sy Laws**: Clear, intuitive definitions of the Horizontal ($R_n^k < R_n^{k+1}$), Vertical ($R_{n+1}^k < R_n^k$), and Diagonal ($R_n^k < R_{n+1}^{k+1}$) laws.
  - Concrete examples demonstrating how to interpret these laws on a sample configuration to make them easy to comprehend and explore further.
  - Explanation of the relations between the laws (e.g., Vertical + Diagonal => Horizontal) and the new complex SbL $\beta$ log-log regression metric.
- **`sbl_global_summary.html`**
  - Global averages and aggregated ordering statistics across all languages.
  - Analysis by language family (e.g., percentage compliance with $Size(R_1) < Size(R_2)$).
- **`sbl_laws_compliance.html`**
  - The comprehensive master table displaying the Horizontal, Vertical, and Diagonal law scores (out of 6) for all 180 languages.
  - Includes complex SbL $\beta$ slopes, ratio bounds (Min/Max/GM), and compliance percentages.
- **`sbl_laws_visualizations.html`**
  - Visual distributions of the Sy laws across languages.
  - Interactive log-log scatter plots visualizing the points $(-log(n+1-k), log(R_n^k))$ used to compute the complex SbL $\beta$ regression line.
  - Histograms showing the distribution of Horizontal, Vertical, and Diagonal scores.
- **`sbl_explorer.html` (Interactive Dashboard)**
  - Sortable table of all languages with their key SBL factors.
  - Clicking a language opens a detailed view (or modal) showing its full Helix Table, AnyOtherSide Table, and specific ordering stats.
- **`sbl_validation.html` (Spot-Check Diagnostic)**
  - A visual "spot-check" page detailing exactly how the laws are computed for reference languages (e.g., French, English, Japanese).
  - Displays the raw Helix table side-by-side with the explicitly extracted pairs (e.g., $R_4^2 < R_4^3$), highlighting which ones pass or fail to yield the final score out of 6.
- **`sbl_typological_maps.html`**
  - Interactive SVG world maps visualizing geographic distribution of SBL effects.
- **`sbl_examples.html`**
  - Links to sample treebank sentences highlighting the verb (red) and its dependents (green).

---

## 3. Implementation Steps

### Phase 1: Data Aggregation & Loader
- [x] Verify that all TSV files in `data/helix_tables/` are complete and up-to-date.
- [x] Create a data-loading utility to parse these TSVs into Python dictionaries, extracting:
  - Average constituent sizes per position
  - Horizontal and diagonal growth factors
  - Ordering statistics (lt, eq, gt)

### Phase 2: Core Generator Setup
- [x] Create `sbl_site.py` inspired by the architecture of `mal_site.py`.
- [x] Re-use or adapt the common CSS (`_COMMON_CSS`), JS for table sorting, and the sticky navigation bar layout (`_nav_bar`).
- [x] Set up the output directory `html_sbl_analyses/` and basic page templates.

### Phase 3: Page Implementation
- [x] **Home Page**: Draft the introductory text and explanatory graphics.
- [x] **Explorer & Compliance Pages**: Implement the main sortable tables (including the new Sy Laws Compliance table). Port the table HTML rendering from `generate_html_examples.py`, but upgrade it to match the new CSS schema.
- [x] **Visualizations**: Build SVG scatter plots for the log-log regressions and score histograms for the Sy laws.
- [x] **Validation Page**: Construct the diagnostic view that explicitly traces the 6 pairs for manual verification on sample languages (French, etc.).
- [x] **Global Summary**: Implement SVG generation for family-level bar charts (e.g., average $Size(R_1)$ vs $Size(R_2)$).
- [x] **Typological Maps**: Adapt the `_generate_svg_world_map` function to accept SBL compliance scores and render color-coded geographic maps.

### Phase 4: Polish & Review
- [x] Ensure consistent navigation across all pages.
- [x] Add tooltips and context menus explaining specific metrics.
- [x] Verify responsiveness and visual hierarchy.
- [x] Update the repository's `README.md` to document the new `sbl_site.py` workflow.
- [x] **Global Matrix (Validation Page)**: Instead of showing just pass/fail (✅/❌), implement a color code indicating the degree of compliance or anti-compliance.
- [x] **Left Side SbL Explanations**: Better explain what is measured and what is longer, specifically addressing: "Compliance with Short-Before-Long on the Left side. Left slopes are negated so Green means compliant."
- [x] **Site-wide Symmetry Check**: Ensure the whole site presents both left and right sides of the verb symmetrically and that the left side is analyzed wherever applicable.

### Phase 5: Significance Analysis
- [x] Add a dedicated Significance Analysis page (`sbl_page_significance.py`) to present significance metrics with simple and extensive explanations.
- [x] Compute Binomial Test (Sign Test) p-values for Horizontal laws using sentence-level counts from TSV files.
- [x] Modify `conll_processing.py` to track the sum of squared lengths and output standard deviations to cached data.
- [x] Compute Welch's t-test for Vertical and Diagonal laws using the variance.
- [x] Display a "Significance Matrix" in the site.
- [ ] Perform ANOVA/Kruskal-Wallis tests across language families and correlations against word order metrics.


### Phase 6: Helix Table & Explorer Page Improvements
- [x] **Left-Side Diagonal Rows:** Add diagonal rows (e.g., `Diag L2-1`) on the left side of the helix tables, mirroring the right side.
- [x] **Modal Dialog Width:** Increase the width of the popup modal in the interactive explorer (`sbl_explorer.html`) to prevent horizontal scrolling.
- [x] **Table Ordering in Modal:** Place the AnyOtherSide helix table (partial configurations) on top of the strict table within the modal view.
- [x] **Helix Table Renaming:** Rename Standard Helix Table to "strict - nothing on opposite side" and AnyOtherSide Helix Table to "unconstrained on opposite side".
- [x] **Vertical Growth Factors:** Include vertical growth factors between adjacent rows in the helix tables (down-to-up on the right side, up-to-down on the left side).
- [x] **Count/Filtering Fixes:** Fix the discrepancy in neighbor pair statistics (e.g., French `R tot=4` between R3 and R4 showing identical counts in strict and unconstrained tables).
- [ ] **Correct Vertical Growth Factors & Directions:**
  - **Right Side:** Currently, the vertical factor (comparing `R tot=n` to `R tot=n-1`) uses an up-right pointing arrow (`↗`). Since this goes from `n` to `n-1` (which is visually downward in the table layout), update it to use a **down-pointing arrow** (e.g., `↓` or `↘`).
  - **Left Side:** Currently, the vertical factor is computed from `L tot=n-1` to `L tot=n` (visually downward). Change it to compute from more to less constituents (from `L tot=n` to `L tot=n-1`, which is visually upward in the table layout). This requires inverting the value ($1/x$) and displaying it with an **up-pointing arrow** (., `↑`) to match the upward comparison direction.


### Phase 7: Outer Constituent Effect Metrics & Plots
- [x] **Diagonal vs. Rest Geometric Means:**
  - Compute the unweighted geometric mean of the three outer constituent cells:
    - Right side: $R_2^2$, $R_3^3$, $R_4^4$ (diagonal cases)
    - Left side: $L_2^2$, $L_3^3$, $L_4^4$
  - Compute the unweighted geometric mean of the remaining cells:
    - Right side: $R_1^2$, $R_1^3$, $R_2^3$
    - Left side: $L_1^2$, $L_1^3$, $L_2^3$
  - Add these values to the helix tables.
- [x] **Outer Constituent Effect Ratios:**
  - Compute the ratio of the outer diagonal mean divided by the rest mean (e.g., Right/Left Outer Constituent Effect).
  - Compute the geometric standard deviation (GSD) for both groups of cells.
- [x] **Typological Correlation Plots:**
  - Generate scatter plots correlating the VO-OV word order score against the Right Outer Constituent Effect.
  - Generate a similar scatter plot for the Left Outer Constituent Effect.
  - Embed these plots in the visualizations page (`sbl_laws_visualizations.html`).


-- helix tables should close on ESC

### Phase 8: Language-Specific Outer Effect Graphs Page
- [x] **Plot Generation for Left/Right Averages**:
  - Generate clean SVG plots for both Left and Right outer constituent size curves.
  - **Right Graph**:
    - 3 curves: $n=2$ (plots $R_2^k$), $n=3$ (plots $R_3^k$), $n=4$ (plots $R_4^k$).
    - x-axis: Position $k \in \{1, 2, 3, 4\}$ (distance increasing from the verb).
    - y-axis: Average constituent size (in words).
  - **Left Graph**:
    - 3 curves: $n=2$ (plots $L_2^k$), $n=3$ (plots $L_3^k$), $n=4$ (plots $L_4^k$).
    - x-axis: Position $k \in \{4, 3, 2, 1\}$ (inverted visual order: 4 on the far left, 1 on the right).
    - y-axis: Average constituent size (in words).
  - **Scale Alignment**:
    - Ensure both Left and Right plots for the same language share identical Y-axis limits (`ylim`) based on the minimum and maximum values across both sides to allow direct visual comparison.
- [x] **Outer Effect Graphs Page**:
  - Create a new page `sbl_outer_effects.html` listing all languages.
  - For each language, show the Left Outer Effect graph and Right Outer Effect graph side-by-side.
  - Add navigation link to `sbl_html_utils.py` and call generation in `sbl_site.py`.
- [x] **Modal Dialog Graph Integration**:
  - Embed the generated Left and Right graphs directly into the corresponding language's modal popup on the Interactive Explorer (`sbl_explorer.html`).
- [x] add dot for n=1 to the outer effect graphs.
- [x] instead of showing the outer effect graphs in the helix popup, show them directly in a small version in the language table. 


-- add plot outer constituent effect vs head-initiality (look for the term in the existing code)