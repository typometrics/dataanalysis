# Verb-Centered Constituent Size Analysis

This document explains the "Verb-Centered Constituent Size Analysis" implemented in this repository.

## Overview

The Verb-Centered Constituent Size Analysis computes and visualizes the average size of constituents (dependents) relative to the verb, grouped by the total number of dependents on each side (Left/Right).

The output is a table where:
- Columns represent positions away from the verb (e.g., L1 is adjacent to V, L2 is second from V).
- Rows represent the complexity of the construction (Total Dependents).

Example Layout:
```
      L2  L1   V   R1  R2
--------------------------
L tot=2:  X   X    V
L tot=1:      X    V
R tot=1:           V   X
R tot=2:           V   X   X
```

## Modules

The implementation relies on two main files:

1.  **`verb_centered_analysis.py`**:
    -   **`compute_average_sizes_table(all_langs_average_sizes_filtered)`**: Aggregates data and calculates simple averages for each position/total configuration.
    -   **`format_verb_centered_table(...)`**: Formats the averages into a readable text table and optionally a TSV file. Handles various display options (factors, arrows).

2.  **`04_data_processing.ipynb`** (Cell "Verb-Centered Constituent Size Analysis"):
    -   Loads the dataset.
    -   Calls `compute_average_sizes_table`.
    -   Calls `format_verb_centered_table` with desired options (factors, diagonals, disorder percentages).
    -   Saves the output to `data/verb_centered_table.txt`.

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
