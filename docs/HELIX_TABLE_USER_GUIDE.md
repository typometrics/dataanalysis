# Helix Table User Guide

This document explains how to read and interpret the "Helix Table" (Verb-Centered Constituent Size Analysis).

## What is this table?

The Helix Table visualizes how the **size of constituents** (subtrees) changes depending on their position relative to the verb. It specifically looks at how "heavy" (long) the dependents are as you move away from the verb.

## Legend: Layout & Terminology

### Columns (Positions)
The table is centered around the Verb (**V**).
*   **V**: The Verb.
*   **R1, R2, R3...** (Right Side): Dependents to the right of the verb.
    *   **R1**: The dependent immediately adjacent to the verb (closest).
    *   **R2**: The second dependent to the right.
    *   And so on.
*   **L1, L2, L3...** (Left Side): Dependents to the left of the verb.
    *   **L1**: The dependent immediately adjacent to the verb (closest).
    *   **L2**: The second dependent to the left.

### Rows (Totals)
The data is grouped by the **Total Number of Dependents** (Tot) that the verb has on that specific side.
*   **R tot=2**: This row contains averages only for verbs that have exactly **2** dependents on the right side.
*   **L tot=3**: This row contains averages only for verbs that have exactly **3** dependents on the left side.

This grouping allows us to see if the position of a constituent (e.g., R1) behaves differently when it is the *only* dependent versus when it is part of a longer chain.

## Values: What do the numbers mean?

### 1. Constituent Size (The Main Numbers)
The values in the position cells (under L1, R1, etc.) represent the **Constituent Size**.
*   **Definition**: The size is measured as the **Word Count** (number of tokens) in the entire dependency subtree headed by that dependent.
*   **Calculation**: We use the **Geometric Mean** (rather than the arithmetic average) to represent the "typical" size. This is because sentence lengths often follow a log-normal distribution, and the geometric mean is less sensitive to extreme outliers (like one incredibly long sentence).

### 2. Growth Factors (The Arrows)
Between the position columns, you will often see values with arrows (e.g., `×1.5 →`). These represent the **Growth Factor**.
*   **Definition**: The ratio between the sizes of two adjacent positions.
*   **Calculation**: This is the **Geometric Mean of the ratios**. For each sentence, we calculate `freq(outer) / freq(inner)` (or vice versa), and then average these ratios.
*   **Arrows**: The arrow points in the direction of the growth calculation (Numerator / Denominator).
    *   `A → B` means the factor is calculated as **Size(B) / Size(A)**.
    *   `A ← B` means the factor is calculated as **Size(A) / Size(B)**.
    *   **Example**: `×1.5 →` between R1 and R2 means that, on average, R2 is **1.5 times larger** than R1.

### 3. Comparison Triples (< = >)
(If enabled) You may see triples like `(<30=10>60)`.
*   These show the percentage of times the ordering relationship holds between two adjacent constituents.
*   **<**: % of times the left item is smaller than the right item.
*   **=**: % of times they are equal size.
*   **>**: % of times the left item is larger than the right item.

## Summary Rows (Marginal Means)

At the top of the table (or bottom, depending on format), you will see summary rows labelled **M Vert** and **M Diag**.

### M Vert (Vertical Marginal Mean)
Summarizes the column vertically.
*   It calculates the average size of a specific position (e.g., R1) across **all** Total configurations grouped together.
*   **Use case**: "How big is the first right dependent in general, regardless of how many other dependents follow it?"

### M Diag (Diagonal Marginal Mean)
Summarizes the "diagonals" of the table. A diagonal tracks a structural position relative to the *end* of the sequence.
*   **Diag 0 (Longest)**: Tracks the **Outermost** dependent.
    *   Average of: L1 (in Tot=1), L2 (in Tot=2), L3 (in Tot=3)...
    *   **Use case**: "How big is the last element of the chain as the chain gets longer?"
*   **Other Diagonals**: Track the "Second from last", "Third from last", etc.

### 6. Row Statistics (Comment Column)
At the end of each row, you will see a comment block with summary statistics: `[GM: X.XX | Global: Y.YY | N=... ]`
*   **GM (Local)**: The Average Constituent Size for this specific configuration row.
*   **Global**: The Average Constituent Size (Geometric Mean) of the *entire sentence* (all dependents) for sentences matching this row.
    *   For Standard Tables (Zero-Other-Side), GM and Global are identical.
    *   For AnyOtherSide Tables, they differentiate between the local side weight and global sentence complexity.
*   **N**: Samples (sentences) observed for this row.
*   **Slope**: Linear regression slope of sizes along the row (if available).

### 7. Validation Warnings
*   **Rare Configurations**: A footer `⚠️ Rare Configurations (<10 samples)` will appear if any row has fewer than 10 observed sentences. These rows should be interpreted with caution.

## The "Helix" Concept
The name "Helix" comes from the visualized pattern of growth. By tracking both the **Vertical** trends (fixed position, increasing total valency) and **Horizontal** trends (fixed valency, moving outwards), we can observe 2D vector fields of syntactic weight. In many languages, these factors form consistent spiraling or "helical" patterns when plotted.
