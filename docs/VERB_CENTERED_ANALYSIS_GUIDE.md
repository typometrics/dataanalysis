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

## Computation and Options

The analysis provides several visualization options to show not just the sizes, but their relative "growth" or change.

### 1. Simple Averages
Shows the raw average constituent size ($X$) at each position.
-   **Status**: **Available**.
-   **Usage**: Default behavior.

### 2. Horizontal Growth (Left to Right)
Displays the factor of growth between horizontally adjacent constituents, proceeding strictly Left to Right.
-   **Calculation**:
    -   **Right Dependents** ($V \rightarrow R1 \rightarrow R2$): Factor = $R_{pos} / R_{pos-1}$ (Growth outwards).
    -   **Left Dependents** ($L2 \rightarrow L1 \rightarrow V$): Factor = $L_{inner} / L_{outer}$ (e.g. $L1/L2$).
-   **Visual**: Arrows point Right ($\rightarrow$).
-   **Status**: **Available** (use `show_horizontal_factors=True` and `arrow_direction='rightwards'`).

### 3. Horizontal Growth (Right to Left)
Displays factors calculated from Right to Left.
-   **Status**: **Partially Available**.
    -   The `arrow_direction='diverging'` (default) mode calculates "Outward" growth.
        -   **Left Side** ($L1 \leftarrow L2$): Calculates $L2/L1$? No, calculates $L_{outer}/L_{inner}$ with arrow $\leftarrow$. This represents Leftward growth (Right-to-Left).
        -   **Right Side** ($R1 \rightarrow R2$): Calculates $R_{outer}/R_{inner}$ with arrow $\rightarrow$. This is Left-to-Right.
    -   **Note**: There is currently no option to force "Right-to-Left" arrows ($\leftarrow$) on the Right side (calculating $R_{inner}/R_{outer}$).

### 4. Diagonal Growth (Up Right)
Displays growth factors between aligned constituent positions of adjacent "Total" rows, assuming an "Up-Right" visual flow (from Lower Row to Upper Row).
-   **Context**: Typically connects row `Tot=N-1` to row `Tot=N` (e.g., $VXXX \rightarrow VXXXX$).
-   **Calculation**: Factor = $Value_{Tot} / Value_{Tot-1}$ (at same position index).
-   **Status**: **Available** (use `show_diagonal_factors=True`). Current implementation hardcodes the direction as "Up Right" ($\nearrow$), connecting the smaller construction (below) to the larger construction (above).

### 5. Diagonal Growth (Down Left)
Inverse of Option 4. Displays growth/shrinkage factors going from a larger construction to a smaller one (e.g., $VXXXX \rightarrow VXXX$).
-   **Status**: **Not Available**.
    -   The current code only computes the "Up Right" diagonal factor ($Tot / Tot-1$). It does not support a "Down Left" calculation ($Tot-1 / Tot$ with arrow $\swarrow$).

### 6. Order Comparison Triples
Instead of showing a single growth factor, this option displays the percentage distribution of size relations between adjacent constituents.
-   **Output Format**: `X% < | Y% = | Z% >`
-   **Meaning**: In the pair $(A, B)$ (where $A$ is to the left of $B$), what % of time is $Size(A) < Size(B)$, etc.
-   **Right Side ($V \rightarrow R1 \rightarrow R2$)**: Comparing $R_{pos}$ vs $R_{pos+1}$.
-   **Left Side ($L2 \rightarrow L1 \rightarrow V$)**: Comparing $L_{pos+1}$ vs $L_{pos}$ (reading left-to-right).
-   **Status**: **Available** (use `show_ordering_triples=True`). Requires re-running data processing to collect granular stats.

### 7. Row Average Constituent Size
Displays the average size of *all* constituents in that specific configuration row.
-   **Status**: **Available** (use `show_row_averages=True`).

### 8. Per-Language Analysis
The functions support processing single languages or subsets by filtering the input data dictionary.
-   **Usage**: Pass a dictionary containing only the target language's data to `verb_centered_analysis.format_verb_centered_table`.
-   **Status**: **Available**.

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
