# Verb-Centered Constituent Size Analysis

This document explains the "Verb-Centered Constituent Size Analysis" implemented in this repository.

## Overview

The Verb-Centered Constituent Size Analysis computes and visualizes the average size of constituents (dependents) relative to the verb, grouped by the total number of dependents on each side (Left/Right).

The output is a table where:
- Columns represent positions away from the verb (e.g., L1 is adjacent to V, L2 is second from V).
- Rows represent the complexity of the construction (Total Dependents).

### Standard Helix Tables

Example Layout for exact configurations:
```
      L2  L1   V   R1  R2
--------------------------
L tot=2:  X   X    V
L tot=1:      X    V
R tot=1:           V   X
R tot=2:           V   X   X
```

### AnyOtherSide Helix Tables

In addition to exact configurations, the analysis generates **AnyOtherSide** tables showing patterns where one direction is ignored:

Example Layout for partial configurations:
```
... V X X X X    4.05  →1.33  5.40  →1.18  6.35  →1.08  6.85
                       ↘1.11        ↘1.14        ↘0.99
... V X X X      4.05  →1.33  5.40  →1.18  6.35
                       ↘1.11        ↘1.14
... V X X        4.05  →1.33  5.40
                       ↘1.11
... V X          4.05
... X V X ...    1.63  V      →3.63  5.93
X V ...          1.59
                 ↘1.31
X X V ...        2.22  ←1.40  1.59
                 ↘1.13        ↘1.31
X X X V ...      2.66  ←1.20  2.22  ←1.40  1.59
```

These tables capture patterns where one side's complexity varies independently of the other, while preserving the tot dimension for diagonal factor computation.

**Key Features**:
- **Horizontal Factors** (→/←): Growth between adjacent positions (e.g., R1→R2)
- **Diagonal Factors** (↘): Growth across tot levels (e.g., R2 at tot=2 vs R1 at tot=1)
- **Tot Preservation**: Each row represents a specific tot value on the measured side, with any value on the opposite side

## Modules

The implementation relies on several main files:

1.  **`verb_centered_analysis.py`**:
    -   **`compute_average_sizes_table(all_langs_average_sizes_filtered)`**: Aggregates data and calculates averages for each exact position/total configuration.
    -   **`compute_anyotherside_sizes_table(all_langs_average_sizes)`**: Aggregates data for partial configurations (anyother statistics).
    -   **`generate_mass_tables(...)`**: Generates all table variants (global, individual, family, order, anyotherside).
    -   **`generate_anyotherside_helix_tables(...)`**: Generates AnyOtherSide tables with proper formatting.
    -   **`format_verb_centered_table(...)`**: Formats tables into readable text/TSV/XLSX. Handles various display options (factors, arrows).

2.  **`conll_processing.py`**:
    -   Collects both exact and anyother statistics during tree traversal
    -   Keys with `_anyother` suffix for aggregated partial configurations
    -   Keys with `_anyother_totright_N` and `_anyother_totleft_N` for tot-specific statistics (enables diagonal factors)

3.  **`04_data_processing.ipynb`** (Cell "Generate Helix Tables"):
    -   Loads the dataset.
    -   Calls `generate_mass_tables` to create all table variants.
    -   Saves outputs to `data/tables/` directory.

## Visualization Options

The analysis provides several options to display constituent sizes and their relative growth patterns.

### 1. Simple Averages
Shows the raw average constituent size ($X$) at each position (default behavior).

### 2. Horizontal Growth (Left to Right)
Displays growth factors between horizontally adjacent constituents, proceeding left to right:
- **Right Dependents** ($V \rightarrow R1 \rightarrow R2$): Factor = $R_{pos} / R_{pos-1}$ (growth outwards)
- **Left Dependents** ($L2 \rightarrow L1 \rightarrow V$): Factor = $L_{inner} / L_{outer}$ (e.g., $L1/L2$)
- Arrows point right ($\rightarrow$)
- **Usage**: Set `show_horizontal_factors=True` and `arrow_direction='rightwards'`

### 3. Horizontal Growth (Diverging)
Displays "outward" growth on both sides:
- **Left Side** ($L1 \leftarrow L2$): Calculates $L_{outer}/L_{inner}$ with leftward arrow
- **Right Side** ($R1 \rightarrow R2$): Calculates $R_{outer}/R_{inner}$ with rightward arrow
- **Usage**: Set `show_horizontal_factors=True` and `arrow_direction='diverging'` (default)

### 4. Diagonal Growth
Displays growth factors between aligned positions in adjacent "Total" rows (connects row `Tot=N-1` to row `Tot=N`):
- **Calculation**: Factor = $Value_{Tot} / Value_{Tot-1}$ (at same position index)
- **Direction**: Up-right ($\nearrow$), from smaller to larger construction
- **Usage**: Set `show_diagonal_factors=True`

### 5. Order Comparison Triples
Shows percentage distribution of size relations between adjacent constituents:
- **Format**: `X% < | Y% = | Z% >`
- **Meaning**: What percentage of time is $Size(A) < Size(B)$, equal, or greater
- **Right Side** ($V \rightarrow R1 \rightarrow R2$): Comparing $R_{pos}$ vs $R_{pos+1}$
- **Left Side** ($L2 \rightarrow L1 \rightarrow V$): Comparing $L_{pos+1}$ vs $L_{pos}$
- **Usage**: Set `show_ordering_triples=True` (requires granular stats from data pipeline)

### 6. Row Average Constituent Size
Displays the average size of all constituents in each configuration row.
- **Usage**: Set `show_row_averages=True`

### 7. Per-Language Analysis
Generate tables for specific languages or subsets by filtering the input data dictionary.
- **Usage**: Pass filtered dictionary to `verb_centered_analysis.format_verb_centered_table`

## Usage Example

To generate the table with new options:

```python
import verb_centered_analysis

# Compute averages (and assuming ordering_stats is available from data pipeline)
# ...

print(verb_centered_analysis.format_verb_centered_table(
    averages,
    show_horizontal_factors=True,
    show_ordering_triples=True,   # Replaces arrows with < = > stats
    ordering_stats=stats,         # Required for triples
    show_row_averages=True,       # Adds [Avg: X.XX] at end of row
    arrow_direction='rightwards' 
))
```
