# Helix Computation for Language Families: Exploration and Verification

This document explores the code responsible for generating Helix Tables for Language Families (e.g., `FAMILY_Caucasian_table.tsv`). It verifies how values are selected, averaged, and formatted.

## 1. Generation of Family Tables

Family tables are generated in `verb_centered_analysis.py` within the `generate_mass_tables` function.

**Code Reference:** `verb_centered_analysis.py`
```python
# 2. PER-FAMILY AVERAGE
# Group languages by family
family_langs = {}
for lang in all_langs_average_sizes:
    # ... grouping logic ...
    family_langs[group][lang] = all_langs_average_sizes[lang]

# ...
for family, langs_data in family_langs.items():
    family_avgs = compute_average_sizes_table(langs_data)
    
    # NEW LOGIC (as of update):
    if ordering_stats:
        family_ordering = compute_averaged_ordering_stats(list(langs_data.keys()), ordering_stats)
    else:
        family_ordering = compute_aggregate_ordering_stats(langs_data)
    
    # ... formatting call ...
```

The process involves two distinct types of aggregation:
1.  **Metric Averaging** (`compute_average_sizes_table`): Computes the "Average Language" metrics (Sizes and Factors) using Geometric Means.
2.  **Ordering Statistics** (`compute_averaged_ordering_stats`): Computes the "Average Voting Pattern" by averaging the sentence-level percentages of each language.

---

## 2. Averaging of Metrics (Sizes and Factors)

The values for Sizes (e.g., `2.449`) and Growth Factors (e.g., `x0.82->`) are computed using the **Geometric Mean** of the values from **all languages in the family**.

**Code Reference:** `verb_centered_analysis.py` -> `_compute_sizes_and_factors_generic`

### Size Averaging
For a given position (e.g., `right_1_totright_4`), the code computes the geometric mean of the sizes across all languages.
*   **What is averaged:** The log of the constituent size for each language.
*   **Weighting:** All languages are weighted equally (1 language = 1 vote). It does NOT weight by the number of sentences in each treebank.

### Factor Averaging
Growth factors (e.g., `x0.82`) are also computed as the Geometric Mean of the individual language factors.
*   **What is averaged:** The growth factor (ratio) for each language.
*   **Result:** This produces the `x0.82` value. It represents the "typical" growth factor for a language in this family.

---

## 3. Ordering Statistics (Triples)

The values in parentheses, e.g., `(<33=0>67)`, are **Ordering Statistics**.

### Previous Implementation (Voting)
Previously, these were consistent with "Language Voting": identifying whether each language grew or shrank, and then counting the languages.
*   Language A grows? Yes.
*   Language B grows? Yes.
*   Language C shrinks? Yes.
*   Result: `(<67=0>33)` (2/3 grow).
*   **Issue:** For small families (N=3), values were always multiples of 33%.

### New Implementation (Average of Averages)
The code has been updated to use `compute_averaged_ordering_stats`. This averages the **internal distributions** of the languages.

**Algorithm:**
1.  For each language, retrieve its sentence-level statistics (e.g., Lang A has 60% of sentences growing, Lang B has 40%, Lang C has 80%).
2.  Average these percentages: `(60 + 40 + 80) / 3 = 60%`.
3.  Result: `(<60=0>40)`.

**Result:**
This provides a smoother value that reflects the average internal consistency of the languages in the family, rather than a discretized vote count.
*   **N Value:** The `N=` value shown in the table comments (if visible) will now be the sum of the total sentences across all languages in the family, providing context on the sample size backing these averages.

---

## 4. Interpretation of Values

### Interpretation of `(<lt = eq > gt)`

The tuple is displayed as `(< LT_Percentage = EQ_Percentage > GT_Percentage)`. However, the meaning of `lt` (`<`) and `gt` (`>`) depends on the side (Left vs. Right) because of how positions are indexed.

#### Right Side (e.g., `R1 -> R2`)
*   Comparison: `val_a` (R1, Near) vs `val_b` (R2, Far)
*   **`lt` (<)**: `R1 < R2` → **Growth** (Size increases outwards).
*   **`gt` (>)**: `R1 > R2` → **Shrinkage** (Size decreases outwards).
*   **Display:** `(<Growth% = Equal% > Shrinkage%)`

**Example:** `(<60=0>40)` means on average, 60% of sentences in these languages show growth at this position.

#### Left Side (e.g., `L2 <- L1`)
*   Comparison: `val_a` (L2, Far) vs `val_b` (L1, Near)
*   **`lt` (<)**: `L2 < L1` → **Shrinkage** (Size decreases outwards from L1 to L2).
*   **`gt` (>)**: `L2 > L1` → **Growth** (Size increases outwards from L1 to L2).
*   **Display:** `(<Shrinkage% = Equal% > Growth%)`

**Example:** `(<30=0>70)` means on average, 70% of sentences in these languages show growth at this position.
