# Word Order Classification (VO/OV/NDO)

## Overview

The pipeline implements a **tripartite classification** of word order based on verb-object ordering patterns extracted from Universal Dependencies treebanks.

## Classification System

### Thresholds

Languages are classified into three categories based on their **VO score** (proportion of objects appearing to the right of the verb):

- **VO (Verb-Object)**: `vo_score > 0.666` (>66.6% objects to the right)
- **NDO (No Dominant Order)**: `0.333 ≤ vo_score ≤ 0.666` (33.3% to 66.6%)
- **OV (Object-Verb)**: `vo_score < 0.333` (<33.3% objects to the right)

### Threshold Justification

- **Symmetric**: Equal distance from 50% (±16.6 percentage points)
- **WALS-compatible**: Aligns with "No dominant order" category in typological databases
- **Statistical**: ~2/3 majority represents clear dominance
- **Balanced**: Creates roughly equal-sized language categories

## Implementation

### 1. VO Score Computation

**File**: `conll_processing.py`
**Function**: `get_vo_hi_stats(tree)`

For each sentence tree:
- Identifies verb nodes (POS tag = `VERB`)
- Counts objects with dependency relation `obj`
- **Important**: Only counts nominal objects (POS = `NOUN` or `PROPN`)
- Records whether object appears left or right of verb

Aggregation across all trees per language:
- `vo_score = vo_right / vo_total`
- Where `vo_right` = count of right-side objects
- And `vo_total` = total count of object dependencies

### 2. Classification Logic

**File**: `conll_processing.py`
**Function**: `get_all_stats_parallel()`

After computing `vo_score` for each language:

```python
if vo_score is not None:
    if vo_score > 0.666:
        vo_type = 'VO'
    elif vo_score < 0.333:
        vo_type = 'OV'
    else:
        vo_type = 'NDO'
else:
    vo_type = None
```

The classification is saved to `data/vo_vs_hi_scores.csv` with columns:
- `language_code`: ISO 639-3 code
- `vo_score`: Continuous score (0.0-1.0)
- `vo_type`: Categorical classification (VO/OV/NDO)
- `head_initiality_score`: General head-initiality across all dependency types
- `vo_count`: Total object dependencies counted
- `sv_score`: Subject-verb ordering score
- `sv_type`: SV/VS/NDO classification

### 3. Usage in Analysis

**File**: `05_comparative_visualization.ipynb`

The pipeline generates separate plot sets for each word order type:

```python
vo_langs = {l for l in all_langs if lang_to_vo_type.get(l) == 'VO'}
ov_langs = {l for l in all_langs if lang_to_vo_type.get(l) == 'OV'}
ndo_langs = {l for l in all_langs if lang_to_vo_type.get(l) == 'NDO'}
```

Output directories:
- `VO-plots/` - Rigid verb-object languages
- `OV-plots/` - Rigid object-verb languages
- `NDO-plots/` - Flexible order languages

**File**: `06_factor_analysis.ipynb`

WALS validation compares computed `vo_score` and `vo_type` against WALS Feature 83A (Basic Word Order).

## Subject-Verb Classification

The same tripartite system is applied to subject-verb ordering:

- **VS (Verb-Subject)**: `sv_score > 0.666` (>66.6% subjects after verb)
- **NDO_SV**: `0.333 ≤ sv_score ≤ 0.666` (mixed order)
- **SV (Subject-Verb)**: `sv_score < 0.333` (<33.3% subjects after verb)

Where `sv_score` measures the proportion of subjects appearing **after** the verb (VS order).

## Limitations

### Sample Size Effects
- Languages with fewer than 10 object dependencies (MIN_COUNT threshold) are excluded
- Small treebanks may not represent the language's true word order flexibility
- Genre effects: Some treebanks contain formal text (rigid order) vs. spoken text (flexible)

### Dependency-Based Measurement
- Only direct objects (`obj` relation) are counted
- Indirect objects (`iobj`), clausal objects (`ccomp`, `xcomp`) use separate metrics
- Word order of other constituents (adverbials, adjectives) not captured by VO score

### Cross-Linguistic Comparability
- UD annotation may vary in consistency across treebanks
- Some languages use different strategies (e.g., object incorporation, clitic doubling)
- NOUN/PROPN filtering excludes pronominal objects, which may have different ordering

## Related Documentation

- [HELIX_TABLE_METHODOLOGY.md](HELIX_TABLE_METHODOLOGY.md) - Dependency relation filtering
- [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md) - Module dependencies
- [GEOMETRIC_MEAN_INFO.md](GEOMETRIC_MEAN_INFO.md) - Statistical aggregation methods
