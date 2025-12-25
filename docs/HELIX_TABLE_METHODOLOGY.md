# Helix Table Production Pipeline

This document details the complete process for generating the "Helix Table" (Verb-Centered Constituent Size Analysis) from raw CoNLL-U treebanks.

## 1. Data Source and Unification

### Universal Dependencies (UD)
- The analysis is currently performed on **Universal Dependencies (UD)** treebanks (e.g., v2.17).
- **Language Code Identification**: Languages are identified using their ISO code (e.g., `en`, `fr`, `zh`) extracted from the CoNLL-U filename prefix.
- **Unification**: All treebanks belonging to the same language code are combined into a single logical dataset for that language. For example, `UD_English-EWT`, `UD_English-GUM`, and `UD_English-LinES` are all unified under the `en` code.
- **Exclusion**: Specific treebanks can be excluded via `excluded_treebanks.txt` (e.g., Akkadian or experimental sets).

### Pre-processing for Parallelism
- Large CoNLL-U files are split into shorter segments (default: 10,000 sentences each) stored in a `_short` directory. This allows processing to be parallelized across multiple CPU cores.

## 2. Statistical Methodology

The core dependency metrics are computed by traversing the dependency trees of every sentence.

### Fractional Counting and Filtering
The analysis specifically targets the complexity around **Verbs**.

- **Governors**: Only nodes with the Universal POS tag `VERB` are considered as heads.
- **Included Dependents**: The following 16 dependency relations are taken into account for constituent size calculations:
    - `nsubj`, `obj`, `iobj`, `csubj`, `ccomp`, `xcomp`, `obl`, `expl`, `dislocated`, `advcl`, `advmod`, `nmod`, `appos`, `nummod`, `acl`, `amod`.
- **Excluded Dependents**: Functional markers and structural relations are ignored, including:
    - `aux`, `mark`, `cop`, `punct`, `root`, `cc`, `conj`, `fixed`, `flat`, `compound`, `list`, `orphan`, `goeswith`, `reparandum`, `dep`.
- **Bastards**: "Bastard" dependents (those whose grammatical governor is not their direct parent in the tree) are included if their attachment point (the ancestor that connects them to the verbal head) has one of the valid relations listed above. The bastard is included in the span of that ancestor node.

**Implementation Note**: These filtering rules are applied in `conll_processing.py` during the span calculation phase, ensuring consistent treatment across all analyses.

### Configuration Selection
The Helix Table organizes data by **Side** and **Total Dependents**:
- **Side**: Left (pre-verbal) or Right (post-verbal).
- **Total (Tot)**: The number of dependents on that side of the verb ($tot \in \{1, 2, 3, 4\}$).
- **Position (Pos)**: The index of the dependent relative to the verb (1 = adjacent, 2 = one word away, etc.).

#### Exact vs. Partial Configurations

**Exact Configurations** (Standard Helix Tables):
- Match specific counts on both sides (e.g., VXX = 0 left, 2 right)
- Keys like `right_2_totright_2`, `left_3_totleft_3`

**Partial Configurations** (AnyOtherSide Tables):
- Match one side exactly while **ignoring** the opposite side (not requiring it to be zero)
- Preserve tot dimension on the measured side for diagonal factor computation
- Three types:
  - **Any-Left** (`... V X X`): Any number of left dependents, N right dependents
    - Example: `VXX_anyleft` includes all verbs with exactly 2 right dependents, regardless of whether they have 0, 1, 2, or more left dependents
    - Keys: `right_2_anyother` (aggregated), `right_2_anyother_totright_2` (with tot for diagonals)
  - **Any-Right** (`X X V ...`): N left dependents, any number of right dependents
    - Example: `XXV_anyright` includes all verbs with exactly 2 left dependents, regardless of right side
    - Keys: `left_2_anyother` (aggregated), `left_2_anyother_totleft_2` (with tot for diagonals)
  - **Any-Both** (`... X V X ...`): Bilateral with any total counts
    - Example: `XVX_anyboth` includes all verbs with 1 dependent on each side, any totals
    - Keys like `xvx_left_1_anyother`, `xvx_right_1_anyother`

These partial configurations capture patterns where one direction's complexity matters independently of the other, providing a more nuanced view of language structure. The tot dimension is preserved for the measured side, enabling diagonal growth factor computation just as in standard Helix tables.

### Geometric Mean (GM)
To account for the non-linear distribution of constituent sizes, **Geometric Means** are used instead of arithmetic averages for all aggregations:
- **Size GM**: $\exp(\text{mean}(\ln(\text{sizes})))$
- **Factor GM**: $\exp(\text{mean}(\ln(\text{size}_A / \text{size}_B)))$
- **Thinning**: Data points with fewer than 10 occurrences (`MIN_COUNT = 10`) are discarded to ensure statistical reliability.

## 3. Helix Table Layout

The visualization (Helix Table) is produced from the aggregated statistical cache.

### Core Logic
- **V-Center**: The verb "V" is the anchor point.
- **Growth Direction** (configurable via `arrow_direction` parameter):
    - **Default "diverging" mode**:
        - **Right Side**: Factors represent growth radiating away from the verb ($R_{pos} \rightarrow R_{pos+1}$). Arrows point right (**→**).
        - **Left Side**: Factors represent growth radiating away from the verb ($L_{pos} \leftarrow L_{pos-1}$). Arrows point left (**←**).
    - **Alternative modes**: `rightwards`, `left_to_right`, `right_to_left` can reverse arrow directions to explore different hypotheses about growth patterns.

### Marginal Summary Rows
When `show_marginal_means=True` (default), two summary rows are generated for each side:

- **M Vert (Vertical Marginal Means)**: 
    - **Size Columns**: Shows the Geometric Mean of constituent sizes across all `tot` values for each position column.
        - Example: M Vert for R2 = GM of {R2 at tot=2, R2 at tot=3, R2 at tot=4}
    - **Factor Columns**: Shows the Geometric Mean of horizontal growth factors for that position transition across all `tot` values.
        - Example: Factor between R2 and R3 = GM of {R3/R2 at tot=3, R3/R2 at tot=4}
        
- **M Diag (Diagonal Marginal Means)**: Summarizes trends across "diagonals" (trajectories where position increases with tot).
    - **Diagonal 0** (Longest): R1T1 → R2T2 → R3T3 → R4T4 (or L1T1 → L2T2 → L3T3 → L4T4)
    - **Diagonal 1** (Medium): R1T2 → R2T3 → R3T4
    - **Diagonal 2** (Short): R1T3 → R2T4
    - Each diagonal summary includes:
        - The Geometric Mean of constituent sizes along that diagonal
        - The Geometric Mean of growth factors between adjacent positions on that diagonal
    - **Arrow Direction**: Diagonal arrows use the diagonal arrow symbol (↗ or ↙) to indicate growth along the diagonal trajectory.

### Output Formats
- **Text/TSV**: Fixed-width text for reports and tab-separated values for further analysis.
- **Excel (.xlsx)**: A high-fidelity, styled grid with color-coded highlighting for factors and marginal means.

## 4. AnyOtherSide Helix Tables

In addition to standard Helix tables, the pipeline generates **AnyOtherSide** tables that show constituent sizes for partial configurations.

### Table Structure
AnyOtherSide tables use the same format as standard Helix tables but with special row labels using the "..." notation:

**Upper Section** (Any-Left patterns):
```
... V X X X X    [sizes for position 1-4 with any left]
                 [diagonal factors: ↘1.XX  ↘1.XX  ↘1.XX]
... V X X X      [sizes for position 1-3 with any left]
                 [diagonal factors: ↘1.XX  ↘1.XX]
... V X X        [sizes for position 1-2 with any left]
                 [diagonal factors: ↘1.XX]
... V X          [sizes for position 1 with any left]
```

**Middle Row** (Any-Both pattern):
```
... X V X ...    [bilateral sizes with any totals]
```

**Lower Section** (Any-Right patterns):
```
X V ...          [sizes for position 1 with any right]
                 [diagonal factors: ↘1.XX]
X X V ...        [sizes for position 1-2 with any right]
                 [diagonal factors: ↘1.XX  ↘1.XX]
X X X V ...      [sizes for position 1-3 with any right]
                 [diagonal factors: ↘1.XX  ↘1.XX  ↘1.XX]
X X X X V ...    [sizes for position 1-4 with any right]
```

### Tot Dimension Preservation
Unlike the aggregated `_anyother` keys (e.g., `right_2_anyother`), which combine all tot levels, AnyOtherSide tables **preserve the tot dimension for the measured side**:
- Each row represents verbs with exactly N dependents on the measured side (tot=N)
- The opposite side can have any count (hence "any other side")
- Keys like `right_2_anyother_totright_2` track position 2 when tot=2 on the right side
- This enables **diagonal growth factors** comparing R2 at tot=2 vs R1 at tot=1

### Growth Factors
AnyOtherSide tables include both types of growth factors:

**Horizontal Factors** (→ or ←):
- Compare adjacent positions at the same tot level
- Right side: R1 → R2 → R3 (moving outward from verb)
- Left side: L3 ← L2 ← L1 (moving outward from verb)
- Computed from aggregated `_anyother` keys

**Diagonal Factors** (↘):
- Compare same position across different tot levels
- Right side: R2 at tot=2 vs R1 at tot=1, R3 at tot=3 vs R2 at tot=2
- Left side: L2 at tot=2 vs L1 at tot=1, L3 at tot=3 vs L2 at tot=2
- Computed from `_anyother_totright_N` and `_anyother_totleft_N` keys
- Show growth as constructions increase in complexity

### Generation
- Function: `generate_anyotherside_helix_tables()` in `verb_centered_analysis.py`
- Computation: `compute_anyotherside_sizes_table()` computes both aggregated and tot-specific statistics
- Generated for all languages during mass table generation
- Saved as `Helix_{LanguageName}_{code}_AnyOtherSide.tsv` and `.xlsx` (note: "AnyOtherSide" suffix for better sorting)
- Includes both horizontal and diagonal growth factors

### Use Cases
- Analyzing asymmetric dependencies where one side's complexity varies independently
- Comparing languages where one direction shows consistent patterns regardless of the other
- Identifying universal trends that hold across different construction complexities
- Studying how constituent size grows with construction complexity (diagonal factors) independent of the opposite side
