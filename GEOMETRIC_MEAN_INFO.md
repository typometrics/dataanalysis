# Geometric Mean Computation in Helix Tables

This document explains the mathematical methodology behind the values presented in the Helix Tables (Verb-Centered Constituent Size Analysis).

## Overview

All "Average Size" and "Growth Factor" values in the Helix Tables are computed using **Geometric Means (GM)** rather than arithmetic means. This choice is made to account for the non-linear, often Zipfian distribution of linguistic constituent sizes, where arithmetic means can be heavily skewed by outliers (very long constituents).

The General Formula for the Geometric Mean of a set of $n$ values $\{x_1, x_2, ..., x_n\}$ is:

$$ GM = \sqrt[n]{x_1 \cdot x_2 \cdot ... \cdot x_n} = \exp\left( \frac{1}{n} \sum_{i=1}^{n} \ln(x_i) \right) $$

In our implementation, we use the log-sum method (second form) to prevent numerical overflow and facilitate efficient aggregation.

---

## 1. Data Source & Filtering

The values are derived from **Universal Dependencies (UD)** treebanks. The processing pipeline (`conll_processing.py`) applies the following filters before computation:

-   **Head**: Must be a `VERB`.
-   **Dependents**: Only specific relations (core arguments, obliques, etc.) are included. Functional words (`det`, `case`, `aux`) are generally part of the constituent span but not counted as separate "constituents" relative to the verb.
-   **Bastards**: Discontinuous constituents ("bastards") are "lifted" to their grammatical governor (the verb) and included in the size computation.

---

## 2. Computation Levels

The computation happens in three distinct stages/levels. It is crucial to understand that **weighting** differs at each level.

### Level 1: Position Averages (Per Language)
*Calculated in `conll_processing.py`*

For a specific language (e.g., English), and a specific position configuration (e.g., "Right side, 1st position, Total dependents=2"), we compute the mean over **all occurrences in the corpus**.

-   **Input**: Every single instance of a constituent found in the treebank that matches the position criteria.
-   **Computation**: $\exp(\frac{1}{N} \sum \ln(\text{size}_i))$
-   **Weighting**: **Implicitly Weighted by Frequency**.
    -   Since we sum over all corpus instances, frequent constructions contribute more to the mean.
    -   Example: If short constituents appear 1000 times and long ones 10 times, the mean will be very close to the short size.

### Level 2: Group Aggregation (Cross-Language)
*Calculated in `verb_centered_analysis.py` -> `compute_average_sizes_table`*

When generating a table for a *group* of languages (e.g., "All OV Languages" or "Average of All Languages"), we aggregate the Level 1 results.

-   **Input**: The Geometric Mean size for each language in the group.
-   **Computation**: Geometric Mean of the Language Means.
-   **Weighting**: **Unweighted (Equal Language Weight)**.
    -   Each language contributes equally, regardless of its treebank size.
    -   A language with 100,000 sentences has the same influence on the final value as a language with 1,000 sentences.
    -   This prevents large treebanks (like German or Czech) from dominating the statistics of a typological group.

### Level 3: Marginal Means (M Vert, M Diag)
*Calculated in `verb_centered_analysis.py` (Visual Layout)*

The "Marginal Mean" rows/columns (`M Vert` and `M Diag`) in the final table summarize the displayed values.

-   **Input**: The values currently displayed in the table cells (from Level 1 or Level 2).
-   **Computation**: Geometric Mean of the cell values.
-   **Weighting**: **Unweighted (Equal Condition Weight)**.
    -   **M Vert (Vertical)**: The mean of sizes for `Tot=1`, `Tot=2`, `Tot=3`, `Tot=4` is computed treating each `Tot` row equally.
    -   It does **NOT** account for the fact that `Tot=2` might be much more frequent than `Tot=4`.
    -   This provides a "Type-level" summary of the position's behavior across different valencies, rather than a "Token-level" average.

---

## 3. Growth Factors

Growth Factors (displayed as arrows like `×1.23→`) represent the ratio of constituent sizes between two positions.

-   **Formula**: $GM(\text{Ratio}) = \frac{GM(\text{Target})}{GM(\text{Source})}$
-   **Note**: Because we use Geometric Means, the "Mean of Ratios" is mathematically equivalent to the "Ratio of Means" (assuming paired data is consistent, though in our cross-language aggregation we average the logs of ratios directly).

### Types of Factors
1.  **Horizontal**: Ratio between adjacent positions in the same row (e.g., $R_2$ vs $R_1$ for $Tot=2$).
2.  **Diagonal**: Ratio between positions in different rows, following a trajectory where new dependents are added (e.g., $R_2$ at $Tot=2$ vs $R_3$ at $Tot=3$).

---

## Summary Table

| Metric | Context | Data Points | Weighting |
| :--- | :--- | :--- | :--- |
| **Cell Value (One Lang)** | Single Cell (e.g., R1, Tot=2) | All corpus occurrences | **Frequency-weighted** |
| **Cell Value (Group)** | Single Cell | One mean per language | **Unweighted** (1 Lang = 1 Vote) |
| **M Vert / M Diag** | Marginal Summary | Table cells (Tot=1..4) | **Unweighted** (1 Tot = 1 Vote) |
