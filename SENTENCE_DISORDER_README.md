# Sentence-Level Disorder Analysis

## Overview

The disorder analysis now supports two approaches:

1. **Average-level disorder** (original): Checks if the average constituent sizes are ordered
   - Result: Binary flag per language (ordered or disordered)
   - Disadvantage: Produces discrete values in analysis (0 or 1), masking nuance.

2. **Sentence-level disorder** (new): Checks comparison statistics for every pair of adjacent constituents across all sentences.
   - Result: Continuous percentage per language (0.0 - 100.0%)
   - Advantage: Provides a granular view of how often a language deviates from the "Short-before-Long" (or equivalent) preference.

## Computation Logic

### 1. Granular Comparisons
For every sentence and every suitable configuration (e.g., Verb with 2 Right Dependents), we identify adjacent pairs of dependents. For each pair $(D_1, D_2)$, we compare their sizes (number of words):

- **Less Than (<)**: Size($D_1$) < Size($D_2$)
- **Equal (=)**: Size($D_1$) = Size($D_2$)
- **Greater Than (>)**: Size($D_1$) > Size($D_2$)

These counts are aggregated for each language and configuration.

### 2. Continuous Disorder Score
We define a "Disorder Score" as the percentage of pairs that violate the expected length-minimization ordering preference.

#### Right Dependents (Visual Order: $V \rightarrow R_1 \rightarrow R_2$)
*Expected Order*: Short before Long ($Size(R_1) < Size(R_2)$).
- **Ordered**: Less Than (<)
- **Disordered**: Equal (=) OR Greater Than (>)
- **Score Calculation**:
  $$ \text{Disorder \%} = \frac{\text{Count}(=) + \text{Count}(>)}{\text{Total Pairs}} \times 100 $$

#### Left Dependents (Visual Order: $L_2 \leftarrow L_1 \leftarrow V$)
*Note: Left dependents are indexed by distance from verb. $L_1$ is closest, $L_2$ is further.*
*Visual Sequence*: $L_2, L_1, V$.
*Expected Order*: Long before Short visual sequence ($Size(L_2) > Size(L_1)$)? 
*Wait, standard dependency length minimization prefers the short elements to be closer to the head.*
- If Head is on Right ($L \dots V$), short element should be close to V ($L_1$). Long element far ($L_2$).
- So we expect $Size(L_2) > Size(L_1)$.
- Therefore:
    - **Ordered**: Greater Than (>) ($L_{far} > L_{close}$)
    - **Disordered**: Equal (=) OR Less Than (<)
- **Score Calculation**:
  $$ \text{Disorder \%} = \frac{\text{Count}(=) + \text{Count}(<)}{\text{Total Pairs}} \times 100 $$

## Architecture

### Where is it computed?

**Notebook 02 (`02_dependency_analysis.ipynb`)** - Section 2b

The sentence-level disorder computation is now integrated into the main parallel processing pipeline in notebook 02, alongside the existing constituent size analysis.

**Benefits of this approach:**
- All CoNLL file parsing happens in one place
- Efficient: trees are parsed only once for both analyses
- Leverages existing parallel processing infrastructure
- Data is ready for downstream analyses in notebook 04

### Code Structure

**`conll_processing.py`** contains the logic for extracting granular stats:

1. `get_ordering_stats(tree, include_bastards=False)`: 
   - Analyzes a single sentence tree
   - Identifying constituent spans (optionally including "bastard" dependents)
   - Comparing sizes of adjacent constituents
   - Returns counts of `<, =, >` for each configuration

**`compute_disorder.py`** aggregates these stats:

1. `compute_disorder_per_language(..., ordering_stats=None)`:
   - Takes the raw granular counts (lt, eq, gt)
   - Applies the Right/Left logic described above
   - Returns a continuous float score (0.0-1.0) for each language configuration

## Usage

### Step 1: Generate sentence-level disorder data

Open `02_dependency_analysis.ipynb` and run section 2b:

```python
# Set to True to enable sentence-level disorder computation
compute_sentence_disorder = True
```

Run the notebook. This will:
- Take 10-30 minutes (processes all sentences in all CoNLL files)
- Generate `data/sentence_disorder_percentages.csv`
- Generate `data/sentence_disorder_percentages.pkl` (containing the granular stats tree)

### Step 2: Analyze results

Open `04_data_processing.ipynb`. The notebook automatically detects `sentence_disorder_percentages.pkl` and uses the granular stats to produce continuous scatter plots.

## Data Format

### sentence_disorder_percentages.pkl
A nested dictionary structure:
```python
{
    'lang_code': {
        ('side', total_dependents, pair_index): {
            'lt': count,
            'eq': count,
            'gt': count
        },
        ...
    },
    ...
}
```
Example key: `('right', 3, 0)` refers to the pair (Pos 1, Pos 2) in a group of 3 right dependents.

## Troubleshooting

### "Scatter plots show discrete horizontal lines"
**Solution**: This indicates the old binary calculation method is being used. Ensure:
1. You have re-run Notebook 02 to generate the granular stats in `.pkl` format.
2. Notebook 04 successfully loads `sentence_disorder_percentages.pkl`.
