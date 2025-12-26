# Diagonal Factors for AnyOtherSide Tables - Implementation Summary

**Date**: December 25, 2025  
**Status**: ✅ Complete

## Overview

Added diagonal growth factor computation to AnyOtherSide Helix tables by preserving the tot dimension for the measured side while ignoring the opposite side.

## Problem

AnyOtherSide tables previously only had horizontal growth factors. The user clarified that:
- **Tot should reflect the measured side**: `... V X X` has tot=2 (2 right dependents), regardless of left side
- **Diagonal factors should compare across tot levels**: Just like in standard Helix tables

## Solution

### 1. Data Collection (`conll_processing.py`)

Added new keys to preserve tot dimension:

**Before**: Only `right_2_anyother` (aggregated across all tot levels)

**After**: 
- `right_2_anyother` (aggregated for horizontal factors)
- `right_2_anyother_totright_2` (tot-specific for diagonal factors)
- `left_2_anyother_totleft_2` (tot-specific for diagonal factors)

**Code Change** (lines 86-98):
```python
# Any-other-side key WITH tot (for diagonal factors)
key_anyother_tot = f'{key_base}_anyother_tot{direction}_{len(kids)}'
position2num[key_anyother_tot] = position2num.get(key_anyother_tot, 0) + 1
if size > 0:
    position2sizes[key_anyother_tot] = position2sizes.get(key_anyother_tot, 0) + np.log(size)
```

### 2. Factor Computation (`verb_centered_analysis.py`)

Updated `compute_anyotherside_sizes_table()` to compute diagonal factors:

**Added Pairs** (lines 223-234):
```python
# Diagonal Right (increasing position with tot)
for pos in range(2, 20):
    key_b = f'right_{pos}_anyother_totright_{pos}'
    key_a = f'right_{pos-1}_anyother_totright_{pos-1}'
    pairs_to_track.append((key_b, key_a))

# Diagonal Left (increasing position with tot)
for pos in range(2, 20):
    key_b = f'left_{pos}_anyother_totleft_{pos}'
    key_a = f'left_{pos-1}_anyother_totleft_{pos-1}'
    pairs_to_track.append((key_b, key_a))
```

### 3. Table Structure (`verb_centered_analysis.py`)

Updated `build_anyotherside_table_structure()` to include diagonal factor rows:

**Structure**:
```
... V X X X X    4.05  →1.33  5.40  →1.18  6.35  →1.08  6.85
                       ↘1.11        ↘1.14        ↘0.99
... V X X X      4.05  →1.33  5.40  →1.18  6.35
                       ↘1.11        ↘1.14
... V X X        4.05  →1.33  5.40
                       ↘1.11
... V X          4.05
```

**Key Features**:
- Value rows show constituent sizes with horizontal factors (→)
- Diagonal factor rows show growth across tot levels (↘)
- Position 1 skipped in diagonal rows (no position 0 to compare with)

## Testing

Created comprehensive test suite:

1. **`test_anyother_with_tot.py`**: Verifies tot-specific keys are collected
2. **`test_complete_diagonal.py`**: End-to-end test from data collection to table generation

**Test Results** (French dev corpus):
- ✅ 42 anyother keys with tot dimension collected
- ✅ 31 diagonal factor keys computed
- ✅ Tables generated with both horizontal and diagonal factors
- ✅ Sample diagonal factors: R2T2/R1T1 = 1.11, R3T3/R2T2 = 1.14

## Documentation Updates

Updated all relevant documentation:

1. **`docs/HELIX_TABLE_METHODOLOGY.md`**:
   - Updated "Exact vs. Partial Configurations" section
   - Completely rewrote "AnyOtherSide Helix Tables" section
   - Documented tot dimension preservation and growth factors

2. **`docs/VERB_CENTERED_ANALYSIS_GUIDE.md`**:
   - Updated AnyOtherSide example with actual factor values
   - Documented tot-specific keys in `conll_processing.py` description

3. **`docs/CONFIG_EXAMPLES_QUICKSTART.md`**:
   - Already up to date (no changes needed)

4. **`docs/PARTIAL_CONFIG_IMPLEMENTATION_PLAN.md`**:
   - Added completion status banner at top

5. **`README.md`**:
   - Updated `verb_centered_analysis.py` module description
   - Updated `conll_processing.py` module description

6. **`04_data_processing.ipynb`**:
   - Updated AnyOtherSide Tables markdown cell with tot dimension info

## Usage

To generate tables with diagonal factors:

1. **Regenerate data** (required to collect new tot-specific keys):
   ```bash
   # Run notebook 04, starting from the data extraction cell
   # This will create new pickle files with _anyother_totright_N keys
   ```

2. **Generate tables**:
   ```python
   from verb_centered_analysis import generate_anyotherside_helix_tables
   
   generate_anyotherside_helix_tables(
       all_langs_average_sizes,
       langnames,
       output_dir='data/tables',
       arrow_direction='right_to_left'
   )
   ```

3. **Output files**:
   - `Helix_{LanguageName}_{code}_AnyOtherSide.tsv`
   - `Helix_{LanguageName}_{code}_AnyOtherSide.xlsx`

## Key Insights

### Conceptual Understanding

**Standard Helix Tables**:
- Have explicit rows for each tot level (tot=1, tot=2, tot=3, tot=4)
- Diagonal factors compare R2 at tot=2 vs R1 at tot=1
- Both tot dimensions present (left and right)

**AnyOtherSide Tables**:
- Each row represents a specific tot on the **measured side**
- Opposite side can have any value (hence "any other side")
- Diagonal factors compare same tot levels: R2 at tot=2 vs R1 at tot=1
- **Key difference**: One tot dimension, not two

### Example Interpretation

For `... V X X` (2 right dependents, any left):
- Includes verbs like: `V X X`, `X V X X`, `X X V X X`, etc.
- All have **tot=2 on the right side**
- Diagonal factor compares this row to `... V X` row (tot=1 on right)

## Files Modified

1. `conll_processing.py` - Added tot-specific anyother keys
2. `verb_centered_analysis.py` - Added diagonal factor computation and table structure
3. `docs/HELIX_TABLE_METHODOLOGY.md` - Updated methodology documentation
4. `docs/VERB_CENTERED_ANALYSIS_GUIDE.md` - Updated guide with examples
5. `docs/PARTIAL_CONFIG_IMPLEMENTATION_PLAN.md` - Added completion status
6. `README.md` - Updated module descriptions
7. `04_data_processing.ipynb` - Updated AnyOtherSide section

## Migration Notes

**For existing projects**:
1. Must regenerate `all_langs_average_sizes_filtered.pkl` to include new keys
2. Run notebook 04 from the data extraction cell onwards
3. Old AnyOtherSide tables (without diagonal factors) will be replaced
4. New filename format places "AnyOtherSide" suffix after language code for better sorting

## Future Work

None required - feature is complete and tested.
