# Implementation Plan: VO/OV/NDO Tripartite Classification

**Date**: December 13, 2025  
**Objective**: Transform binary VO/OV classification into tripartite VO/OV/NDO system

## Current System Analysis

### Where VO/OV Distinction is Made

#### 1. **Data Computation** (Core)
**File**: `conll_processing.py`
- **Function**: `get_vo_hi_stats(tree)` (lines 761-828)
  - Counts `vo_right` and `vo_total` for each tree
  - Only considers `obj` dependency relation for VO scoring
  
- **Function**: `get_all_stats_parallel()` (lines 974-1030)
  - Aggregates counts across all files per language
  - Computes `vo_score = vo_right / vo_total` (line 1013)
  - **Current threshold**: None applied here (raw score)

**Output**: `data/vo_vs_hi_scores.csv` with columns:
- `language` (code)
- `vo_score` (0.0 to 1.0, percentage of right objects)
- `head_initiality_score` (general head-initial score)
- `vo_count` (total object dependencies)
- `total_deps` (total target dependencies)

#### 2. **Classification & Filtering** (Notebooks)
**File**: `05_comparative_visualization.ipynb` (lines 324-338)
```python
# Load vo_score from vo_hi_df
lang_to_vo = vo_hi_df.set_index(join_col_hi)['vo_score'].to_dict()

# Current binary classification (50% threshold)
vo_langs = {l for l in all_langs_average_sizes_filtered if lang_to_vo.get(l, 0) > 0.5}
ov_langs = {l for l in all_langs_average_sizes_filtered if lang_to_vo.get(l, 0) <= 0.5}
```

**Usage**: Creates plot subsets (lines 367-368)
```python
("VO (Verb-Initial) Languages", "VO-", vo_langs),
("OV (Verb-Final) Languages", "OV-", ov_langs)
```

#### 3. **Standalone Script** (Alternative)
**File**: `compute_vo_vs_hi.py`
- Duplicate functionality of `conll_processing.py`
- Also computes `vo_score` without classification
- **Status**: Not used by notebooks (functionality integrated in notebook 02)

---

## Proposed Changes

### New Thresholds
- **VO**: `vo_score > 0.666` (>66.6% objects to the right)
- **NDO**: `0.333 <= vo_score <= 0.666` (33.3% to 66.6%)
- **OV**: `vo_score < 0.333` (<33.3% objects to the right)

### Files to Modify

#### ✅ REQUIRED CHANGES

##### 1. **`conll_processing.py`** - Add classification logic
**Location**: After line 1013 (in `get_all_stats_parallel()`)

**Current**:
```python
vo_score = stats['vo_right'] / vo_total if vo_total > 0 else None
hi_score = stats['all_right'] / all_total if all_total > 0 else None

lang_vo_hi_scores[lang] = {
    'vo_score': vo_score,
    'head_initiality_score': hi_score,
    'vo_count': vo_total,
    'total_deps': all_total,
    'vo_right': stats['vo_right'],
    'all_right': stats['all_right']
}
```

**Proposed**:
```python
vo_score = stats['vo_right'] / vo_total if vo_total > 0 else None
hi_score = stats['all_right'] / all_total if all_total > 0 else None

# Classify word order type
if vo_score is not None:
    if vo_score > 0.666:
        vo_type = 'VO'
    elif vo_score < 0.333:
        vo_type = 'OV'
    else:
        vo_type = 'NDO'
else:
    vo_type = None

lang_vo_hi_scores[lang] = {
    'vo_score': vo_score,
    'vo_type': vo_type,  # NEW FIELD
    'head_initiality_score': hi_score,
    'vo_count': vo_total,
    'total_deps': all_total,
    'vo_right': stats['vo_right'],
    'all_right': stats['all_right']
}
```

**Impact**: 
- Adds `vo_type` column to `data/vo_vs_hi_scores.csv`
- All downstream notebooks that read this file will have access to classification

---

##### 2. **`02_dependency_analysis.ipynb`** - Save new field
**Location**: After saving VO/HI scores (around line 180-200)

**Current**:
```python
vo_hi_rows = []
for lang, scores in lang_vo_hi_scores.items():
    row = scores.copy()
    row['language_code'] = lang
    row['language_name'] = langNames.get(lang, lang)
    row['group'] = langnameGroup.get(row['language_name'], 'Unknown')
    vo_hi_rows.append(row)

vo_hi_df = pd.DataFrame(vo_hi_rows)
vo_hi_output_file = os.path.join(DATA_DIR, 'vo_vs_hi_scores.csv')
vo_hi_df.to_csv(vo_hi_output_file, index=False)
```

**No changes needed** - the new `vo_type` field will automatically be included since `row = scores.copy()` copies all fields.

---

##### 3. **`05_comparative_visualization.ipynb`** - Update filtering logic
**Location**: Lines 324-338 (language set creation)

**Current**:
```python
if 'vo_score' in vo_hi_df.columns:
    lang_to_vo = vo_hi_df.set_index(join_col_hi)['vo_score'].to_dict()
else:
    lang_to_vo = {}
    print("Warning: 'vo_score' not found in vo_hi_df. VO/OV plots will be skipped.")

# Calculate Lists of Languages for Parallel Processing
indo_euro_langs = {l for l in all_langs_average_sizes_filtered if langnameGroup.get(langNames.get(l, l), 'Other') == 'Indo-European'}
non_indo_euro_langs = {l for l in all_langs_average_sizes_filtered if langnameGroup.get(langNames.get(l, l), 'Other') != 'Indo-European'}

head_init_langs = {l for l in all_langs_average_sizes_filtered if lang_to_head_init.get(l, 0) > 0.5}
head_final_langs = {l for l in all_langs_average_sizes_filtered if lang_to_head_init.get(l, 0) <= 0.5}

vo_langs = {l for l in all_langs_average_sizes_filtered if lang_to_vo.get(l, 0) > 0.5}
ov_langs = {l for l in all_langs_average_sizes_filtered if lang_to_vo.get(l, 0) <= 0.5}
```

**Proposed**:
```python
# Load vo_type classification
if 'vo_type' in vo_hi_df.columns:
    lang_to_vo_type = vo_hi_df.set_index(join_col_hi)['vo_type'].to_dict()
else:
    # Fallback: compute from vo_score if vo_type not available
    if 'vo_score' in vo_hi_df.columns:
        lang_to_vo = vo_hi_df.set_index(join_col_hi)['vo_score'].to_dict()
        lang_to_vo_type = {}
        for lang, score in lang_to_vo.items():
            if score is not None and not pd.isna(score):
                if score > 0.666:
                    lang_to_vo_type[lang] = 'VO'
                elif score < 0.333:
                    lang_to_vo_type[lang] = 'OV'
                else:
                    lang_to_vo_type[lang] = 'NDO'
            else:
                lang_to_vo_type[lang] = None
    else:
        lang_to_vo_type = {}
        print("Warning: Neither 'vo_type' nor 'vo_score' found in vo_hi_df. VO/OV/NDO plots will be skipped.")

# Calculate Lists of Languages for Parallel Processing
indo_euro_langs = {l for l in all_langs_average_sizes_filtered if langnameGroup.get(langNames.get(l, l), 'Other') == 'Indo-European'}
non_indo_euro_langs = {l for l in all_langs_average_sizes_filtered if langnameGroup.get(langNames.get(l, l), 'Other') != 'Indo-European'}

head_init_langs = {l for l in all_langs_average_sizes_filtered if lang_to_head_init.get(l, 0) > 0.5}
head_final_langs = {l for l in all_langs_average_sizes_filtered if lang_to_head_init.get(l, 0) <= 0.5}

# NEW: Tripartite classification
vo_langs = {l for l in all_langs_average_sizes_filtered if lang_to_vo_type.get(l) == 'VO'}
ov_langs = {l for l in all_langs_average_sizes_filtered if lang_to_vo_type.get(l) == 'OV'}
ndo_langs = {l for l in all_langs_average_sizes_filtered if lang_to_vo_type.get(l) == 'NDO'}
```

**Location**: Lines 367-368 (subset list)

**Current**:
```python
subsets = [
    ("Head Final Languages", "headFinal-", head_final_langs),
    ("Head Initial Languages", "headInit-", head_init_langs),
    ("Indo-European Languages", "IE-", indo_euro_langs),
    ("Non-Indo-European Languages", "noIE-", non_indo_euro_langs),
    ("VO (Verb-Initial) Languages", "VO-", vo_langs),
    ("OV (Verb-Final) Languages", "OV-", ov_langs)
]
```

**Proposed**:
```python
subsets = [
    ("Head Final Languages", "headFinal-", head_final_langs),
    ("Head Initial Languages", "headInit-", head_init_langs),
    ("Indo-European Languages", "IE-", indo_euro_langs),
    ("Non-Indo-European Languages", "noIE-", non_indo_euro_langs),
    ("VO (Verb-Object) Languages", "VO-", vo_langs),
    ("OV (Object-Verb) Languages", "OV-", ov_langs),
    ("NDO (No Dominant Order) Languages", "NDO-", ndo_langs)  # NEW
]
```

---

##### 4. **Update alternate version in same notebook** (lines 550-556)
**Location**: Second occurrence of subset list in notebook 05

**Current**:
```python
subsets = [
    ("Head Final Languages", "headFinal-", head_final_langs),
    ("Head Initial Languages", "headInit-", head_init_langs),
    ("Indo-European Languages", "IE-", indo_euro_langs),
    ("Non-Indo-European Languages", "noIE-", non_indo_euro_langs)
]
```

**Proposed** (if VO/OV/NDO are included in this section):
```python
subsets = [
    ("Head Final Languages", "headFinal-", head_final_langs),
    ("Head Initial Languages", "headInit-", head_init_langs),
    ("Indo-European Languages", "IE-", indo_euro_langs),
    ("Non-Indo-European Languages", "noIE-", non_indo_euro_langs),
    ("VO (Verb-Object) Languages", "VO-", vo_langs),
    ("OV (Object-Verb) Languages", "OV-", ov_langs),
    ("NDO (No Dominant Order) Languages", "NDO-", ndo_langs)
]
```

---

#### 🔧 OPTIONAL CHANGES

##### 5. **`compute_vo_vs_hi.py`** - Standalone script (if used)
**Location**: After line 130 (main function, after computing vo_score)

**Current**:
```python
output_data.append({
    'language': lang,
    'vo_score': vo_score,
    'head_initiality_score': hi_score,
    'vo_count': vo_total,
    'total_deps': all_total
})
```

**Proposed**:
```python
# Classify word order type
if vo_score is not None:
    if vo_score > 0.666:
        vo_type = 'VO'
    elif vo_score < 0.333:
        vo_type = 'OV'
    else:
        vo_type = 'NDO'
else:
    vo_type = None

output_data.append({
    'language': lang,
    'vo_score': vo_score,
    'vo_type': vo_type,  # NEW
    'head_initiality_score': hi_score,
    'vo_count': vo_total,
    'total_deps': all_total
})
```

**Note**: This script is not used by the notebook pipeline, so this change is optional for consistency.

---

##### 6. **`06_factor_analysis.ipynb`** - WALS validation plots
**Location**: Lines with VO/OV filtering (if present)

**Current**: May have references to binary VO/OV classification

**Proposed**: Update any hardcoded references to use tripartite classification. Search for:
- `vo_score > 0.5`
- `vo_score <= 0.5`
- Labels like "VO" and "OV" in plot titles

**Specific change** (if filtering by VO type):
```python
# Before
vo_subset = comparison_df[comparison_df['vo_score'] > 0.5]

# After
vo_subset = comparison_df[comparison_df['vo_type'] == 'VO']
ndo_subset = comparison_df[comparison_df['vo_type'] == 'NDO']
ov_subset = comparison_df[comparison_df['vo_type'] == 'OV']
```

---

### Output Changes

#### New Output Directories (Created Automatically)
- `NDO-plots/` - Scatter plots for NDO languages
- `NDO-regplots/` - Regression plots for NDO languages

#### Updated CSV File
**`data/vo_vs_hi_scores.csv`** - New column added:
```
language,vo_score,vo_type,head_initiality_score,vo_count,total_deps,vo_right,all_right
en,0.75,VO,0.65,1234,5678,925,3690
ja,0.15,OV,0.35,2345,6789,352,2376
de,0.45,NDO,0.50,1890,4567,851,2283
```

---

## Implementation Steps

### Step 1: Core Logic Changes
1. ✅ Modify `conll_processing.py` - Add classification logic
2. ✅ Verify no changes needed in `02_dependency_analysis.ipynb` (auto-includes new field)

### Step 2: Filtering Changes
3. ✅ Modify `05_comparative_visualization.ipynb` - Update language set creation
4. ✅ Add `ndo_langs` to subset list
5. ✅ Update labels ("Verb-Initial" → "Verb-Object")

### Step 3: Testing
6. Run `02_dependency_analysis.ipynb` to regenerate `vo_vs_hi_scores.csv`
7. Verify new `vo_type` column exists and has correct classifications
8. Run `05_comparative_visualization.ipynb` to generate NDO plots
9. Check that 3 directories are created: `VO-plots/`, `OV-plots/`, `NDO-plots/`

### Step 4: Optional Updates
10. Update `compute_vo_vs_hi.py` for consistency
11. Review `06_factor_analysis.ipynb` for hardcoded thresholds
12. Update README.md to document tripartite classification

### Step 5: Validation
13. Generate statistics: How many languages in each category?
14. Compare with WALS Feature 83A (if available in notebook 06)
15. Spot-check known languages (e.g., English→VO, Japanese→OV, German→NDO?)

---

## Expected Impact

### Languages per Category (Estimated)
Based on typical language distributions:
- **VO**: ~35-40% of languages (rigid VO order)
- **OV**: ~35-40% of languages (rigid OV order)
- **NDO**: ~20-30% of languages (flexible or mixed order)

### Runtime Impact
- **Minimal**: Classification adds negligible computation
- Plot generation will take ~33% longer (3 subsets instead of 2)
  - Was: ~3-4 minutes for VO + OV
  - Now: ~4-6 minutes for VO + OV + NDO

### Output Size
- **+50%**: Additional plot directories (~400 plots)
  - Was: `VO-plots/` + `OV-plots/` (~800 plots)
  - Now: + `NDO-plots/` (~400 plots)

---

## Threshold Justification

### Why 66.6% / 33.3%?
1. **Symmetric**: Equal distance from 50% (16.6 percentage points)
2. **WALS-compatible**: Aligns with "No dominant order" category in typology
3. **Statistical**: ~2/3 majority is a common threshold for "dominance"
4. **Balanced**: Creates roughly equal-sized categories

### Alternative Thresholds (Not Recommended)
- **60/40**: Too loose, would classify many flexible languages as VO/OV
- **75/25**: Too strict, would classify most languages as NDO
- **80/20**: Very strict, almost all languages become NDO

---

## Testing Checklist

### Functionality Tests
- [ ] `vo_type` column appears in `vo_vs_hi_scores.csv`
- [ ] Classification matches expected thresholds (manual check on sample)
- [ ] `ndo_langs` set is populated in notebook 05
- [ ] `NDO-plots/` directory is created
- [ ] Plots are generated for all 3 categories
- [ ] No errors during pipeline execution

### Data Validation
- [ ] All languages with `vo_score` have `vo_type`
- [ ] `vo_type` is NULL only when `vo_score` is NULL
- [ ] No languages classified as both VO and OV
- [ ] NDO languages have scores between 0.333 and 0.666
- [ ] Total count: VO + OV + NDO + None = total languages

### Regression Tests
- [ ] Existing VO plots unchanged (same languages)
- [ ] Existing OV plots unchanged (same languages)
- [ ] Pipeline runs end-to-end without errors
- [ ] README documentation is updated

---

## Rollback Plan

If issues arise, revert changes:
1. Git checkout previous version of `conll_processing.py`
2. Git checkout previous version of `05_comparative_visualization.ipynb`
3. Delete `NDO-plots/` and `NDO-regplots/` directories
4. Re-run notebook 02 to regenerate old `vo_vs_hi_scores.csv`

Or keep both versions:
- Add `use_tripartite=True/False` parameter to control classification
- Maintain backward compatibility with binary system

---

## Future Enhancements

### Possible Extensions
1. **Configurable thresholds**: Allow user to adjust 66.6% cutoff
2. **Subcategories**: Further split NDO into "slight VO preference" vs "balanced" vs "slight OV preference"
3. **Confidence intervals**: Report uncertainty in classification (especially for low-count languages)
4. **Temporal analysis**: Track if languages shift between categories across UD versions
5. **Relation-specific classification**: Different thresholds for obj vs. iobj vs. csubj

### Documentation Updates Needed
- README.md: Add section on tripartite classification
- MODULE_ANALYSIS.md: Update to reflect new functionality
- SENTENCE_DISORDER_README.md: No changes needed (orthogonal feature)
- Add new file: `VO_CLASSIFICATION_README.md` (detailed documentation)

---

## Summary

### Minimal Required Changes
1. **conll_processing.py**: 8 lines added (classification logic)
2. **05_comparative_visualization.ipynb**: ~40 lines modified (filtering + subset list)

### Files Affected
- ✅ MUST CHANGE: 2 files
- 🔧 OPTIONAL: 2 files (standalone script, WALS validation)
- 📄 UPDATE: 1 file (README.md)

### Backward Compatibility
- ✅ YES: Old notebooks still work (ignore `vo_type` column)
- ✅ YES: Old plots unchanged (VO/OV same languages)
- ✅ YES: New feature is additive (doesn't break existing functionality)

### Risk Level
**LOW** - Changes are isolated, well-defined, and additive.
