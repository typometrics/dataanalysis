# Plan: Partial Verb Configurations (Ignoring One Direction)

> **STATUS**: ✅ **COMPLETED** - All features described in this document have been implemented as of December 2025.
> 
> **Key Implementation Details**:
> - ✅ Data collection: `_anyother` keys in `conll_processing.py`
> - ✅ Tot dimension preservation: `_anyother_totright_N` and `_anyother_totleft_N` keys for diagonal factors
> - ✅ HTML generation: Conditional display for partial configurations
> - ✅ AnyOtherSide Helix tables: Full table generation with horizontal and diagonal growth factors
> - ✅ Filename format: `Helix_{LanguageName}_{code}_AnyOtherSide.tsv/xlsx` (for better sorting)
> 
> For current usage, see:
> - `docs/HELIX_TABLE_METHODOLOGY.md` - Complete methodology
> - `docs/VERB_CENTERED_ANALYSIS_GUIDE.md` - Module documentation
> - `docs/CONFIG_EXAMPLES_QUICKSTART.md` - HTML examples usage

## 1. Problem Statement

**Current Behavior:**
- `VXX` matches only verbs with exactly 0 left, 2 right dependents
- `XXV` matches only verbs with exactly 2 left, 0 right dependents
- `XVXX` does NOT match `VXX` pattern (correctly)

**Desired Behavior:**
- Add new "partial" configurations that ignore one direction
- Example: `VXX_anyleft` would match `VXX`, `XVXX`, `XXVXX`, etc.
- Example: `XXV_anyright` would match `XXV`, `XXVX`, `XXVXX`, etc.

---

## 2. Naming Convention

### 2.1 Options Considered

| Pattern | Filename | Pros | Cons |
|---------|----------|------|------|
| `...VXX` | `...VXX.html` | Intuitive | Dots problematic in filenames |
| `anyVXX` | `anyVXX.html` | Clear | Verbose |
| `VXX_anyleft` | `VXX_anyleft.html` | Very explicit | Long |
| `VXX_partial` | `VXX_partial.html` | Short | Less clear what's partial |
| `*VXX` | Bad for filenames | Wildcard | Can't use * |
| `VR2_anyL` | `VR2_anyL.html` | Compact | Less readable |

### 2.2 Recommended Naming

**For HTML files and general use:**
- Pattern with any left: `VXX_anyleft` or `V_R2_anyL`
- Pattern with any right: `XXV_anyright` or `L2_V_anyR`

**For internal keys (shorter):**
- Right dependencies, any left: `right_2_anyleft`
- Left dependencies, any right: `left_2_anyright`

**Examples:**
```
Exact configs:     VXX, XXV, XVXX
Partial configs:   VXX_anyleft, XXV_anyright, XVXX_anyleft
```

---

## 3. Implementation Plan

### 3.1 Core Changes (conll_processing.py)

**File:** `conll_processing.py`

**Function:** `extract_verb_config_examples(tree, include_bastards=False)`

**Current behavior:**
```python
# Creates exact config: 'XX' + 'V' + 'XX' = 'XXVXX'
left_str = 'X' * len(left_kids)
right_str = 'X' * len(right_kids)
config = left_str + 'V' + right_str
```

**New behavior (add alongside current):**
```python
# Store exact config (unchanged)
config_exact = left_str + 'V' + right_str
examples.append((config_exact, head, relevant_kids))

# Also store partial configs
if right_kids:  # Has right deps - create "VXX_anyleft" pattern
    config_partial_right = 'V' + right_str + '_anyleft'
    examples.append((config_partial_right, head, relevant_kids))

if left_kids:  # Has left deps - create "XXV_anyright" pattern
    config_partial_left = left_str + 'V' + '_anyright'
    examples.append((config_partial_left, head, relevant_kids))
```

**Impact:** Each verb with dependencies will generate 1-3 configuration patterns:
- Exact pattern (always)
- Partial right pattern (if has right deps)
- Partial left pattern (if has left deps)

---

### 3.2 HTML Generation (generate_html_examples.py)

**Changes needed:**

#### A. File Generation
Generate separate HTML files for partial configurations:
```
html_examples/French_fr/
  ├── XXV.html              (exact: 2 left, 0 right)
  ├── XXV_anyright.html     (new: 2 left, any right)
  ├── VXX.html              (exact: 0 left, 2 right)
  ├── VXX_anyleft.html      (new: any left, 2 right)
  ├── XXVXX.html            (exact: 2 left, 2 right)
  └── ...
```

#### B. Statistics Display
For partial configs, show additional context:
```html
<h3>Geometric Mean Spans (Partial Configuration)</h3>
<div>Pattern: V + 2 right dependents (ignoring left side)</div>
<div>Matches: VXX, XVXX, XXVXX, etc.</div>
<p><strong>Post-verbal (V X₁ X₂):</strong> 
   X₁: <b>2.15</b> (2.08), X₂: <b>3.45</b> (3.21)
</p>
<p><strong>Note:</strong> Values include examples with varying left-side configurations</p>
```

#### C. Index Page Update
Add section for partial configurations:
```html
<h2>Exact Configurations</h2>
<ul>
  <li>XXV (20 examples) - 2 left, 0 right</li>
  <li>VXX (18 examples) - 0 left, 2 right</li>
  ...
</ul>

<h2>Partial Configurations (Any Left)</h2>
<ul>
  <li>VXX_anyleft (45 examples) - any left, 2 right</li>
  <li>VXXX_anyleft (32 examples) - any left, 3 right</li>
  ...
</ul>

<h2>Partial Configurations (Any Right)</h2>
<ul>
  <li>XXV_anyright (38 examples) - 2 left, any right</li>
  <li>XXXV_anyright (25 examples) - 3 left, any right</li>
  ...
</ul>
```

---

### 3.3 Helix Table Generation

Generate **two types of tables** per language:

1. **Standard Helix Table** (unchanged)
   - Filename: `Helix_English_en.tsv`
   - Shows exact configurations only (e.g., `XXV` = exactly 2 left, 0 right)
   - Current behavior maintained

2. **Any-Other-Side Helix Table** (new)
   - Filename: `Helix_AnyOtherSide_English_en.tsv`
   - Shows statistics ignoring the opposite direction
   - Combines both left and right patterns in one table

**Table structure (AnyOtherSide):**
```
Row                     V    X₁      X₂      X₃      X₄
M Vert Right                 2.15    3.21    4.12    5.45
M Diag Right                 2.15    2.89    3.67
M Vert Left                  1.98    2.87    3.56    4.23
M Diag Left                  1.98    2.34    2.89

... V X X X X           V    1.89    2.45    3.12    5.45  [GM: ... | N=...]
... V X X X             V    1.92    2.78    4.12           [GM: ... | N=...]
... V X X               V    1.85    3.21                   [GM: ... | N=...]
... V X                 V    2.15                           [GM: ... | N=...]
... X V X ...           X    V      X                       [GM: ... | N=...]
X V ...                 X    V                              [GM: ... | N=...]
X X V ...               X    X      V                       [GM: ... | N=...]
X X X V ...             X    X      X      V                [GM: ... | N=...]
X X X X V ...           X    X      X      X      V         [GM: ... | N=...]
```

**Key insight:** 
- Upper rows: Right-side patterns (any left side configuration)
- Middle row: Both sides (e.g., `...XVX...` = any left, any right, but at least 1 each)
- Lower rows: Left-side patterns (any right side configuration)

---

### 3.4 Data Processing Changes

**File:** `conll_processing.py`

**Function:** `get_dep_sizes(tree, ...)`

**Add new accumulation keys:**

Current keys:
```python
'right_1_totright_2'  # Position 1, when total right = 2
'left_2_totleft_3'    # Position 2, when total left = 3
```

New keys (add alongside):
```python
'right_1_anyright'    # Position 1 right, ignore left count
'left_2_anyleft'      # Position 2 left, ignore right count
```

**Implementation:**
```python
# Current code (keep as-is)
key_tot = f'{key_base}_tot{direction}_{len(kids)}'
position2num[key_tot] = position2num.get(key_tot, 0) + 1

# New code (add after above)
# Add marginal key (ignoring other direction)
key_marginal = f'{key_base}_any{direction}'
position2num[key_marginal] = position2num.get(key_marginal, 0) + 1
if size > 0:
    position2sizes[key_marginal] = position2sizes.get(key_marginal, 0) + np.log(size)
```

---

### 3.5 Verb-Centered Analysis Changes

**File:** `verb_centered_analysis.py`

**New function:**
```python
def compute_anyotherside_sizes_table(all_langs_average_sizes_filtered):
    """
    Compute average constituent sizes ignoring the opposite direction.
    
    Combines both:
    - Right-side patterns (ignoring left): right_1_anyleft, right_2_anyleft, ...
    - Left-side patterns (ignoring right): left_1_anyright, left_2_anyright, ...
    
    Returns:
        Dictionary with keys like 'right_1_anyleft', 'left_2_anyright'
    """
    # Similar to compute_average_sizes_table but uses "any other side" keys
    pass
```

**New function:**
```python
def generate_anyotherside_helix_tables(all_langs_average_sizes, langnames, output_dir='data/tables'):
    """
    Generate "Any Other Side" Helix tables that ignore opposite direction.
    
    Creates:
    - Helix_AnyOtherSide_*.tsv/xlsx (one file combining left and right patterns)
    """
    pass
```

---

## 4. File Structure After Implementation

```
html_examples/
├── French_fr/
│   ├── XXV.html                    # Exact: 2L, 0R
│   ├── XXV_anyright.html           # NEW: 2L, any R
│   ├── VXX.html                    # Exact: 0L, 2R
│   ├── VXX_anyleft.html            # NEW: any L, 2R
│   ├── XVX_anyboth.html            # NEW: 1L+1R, any on both sides
│   └── index.html                  # Updated with partial sections
└── ...

data/tables/
├── Helix_English_en.tsv                      # Standard (exact configs)
├── Helix_English_en.xlsx
├── Helix_AnyOtherSide_English_en.tsv         # NEW: Combined any-other-side
├── Helix_AnyOtherSide_English_en.xlsx        # NEW: Combined any-other-side
└── ...
```

---

## 5. Implementation Order

### Phase 1: Data Collection ✅ COMPLETE
1. ✅ Modified `extract_verb_config_examples()` to generate partial configs
2. ✅ Modified `get_dep_sizes()` to accumulate marginal statistics
3. ✅ Tested with debug script on small dataset

### Phase 2: HTML Generation ✅ COMPLETE
4. ✅ Updated `generate_html_examples.py` to create partial config files
5. ✅ Updated index generation to list partial configs
6. ✅ Added explanatory text about partial vs exact configs

### Phase 3: Helix Tables ✅ COMPLETE
7. ✅ Implemented `compute_anyotherside_sizes_table()`
8. ✅ Implemented `generate_anyotherside_helix_tables()`
9. ✅ Updated table formatting to handle any-other-side data
10. ✅ Integrated into mass table generation

### Phase 4: Integration ✅ COMPLETE
11. ✅ Updated `04_data_processing.ipynb` cell ready
12. ✅ All functions integrated into pipeline
13. ✅ Test suite validates all components

---

**Implementation Status**: ✅ COMPLETE

All phases implemented and tested successfully. The system now collects and displays:
- Exact configurations (unchanged behavior)
- Partial configurations in HTML (e.g., `VXX_anyleft.html`)
- Any-Other-Side Helix tables (e.g., `Helix_AnyOtherSide_English_en.tsv`)

**Test Results**: All tests passed ✅
- Statistics collection: anyother keys properly accumulated
- Config examples: partial patterns correctly generated
- Table generation: proper formatting and file output

---

## 6. Example Use Cases

### Use Case 1: Studying Right-Side Complexity
**Question:** How do post-verbal constituent sizes vary regardless of pre-verbal material?

**Answer:** Use `Helix_AnyOtherSide_*.tsv` tables, upper rows
- Compare `... V X X` patterns across languages
- Shows pure right-side patterns without pre-verbal constraints

### Use Case 2: HTML Visualization
**Question:** What do VXX patterns look like across different left-side contexts?

**Answer:** Open `VXX_anyleft.html`
- See examples with 0, 1, 2, 3+ left dependents
- All have exactly 2 right dependents
- Compare sizes across varying left contexts

### Use Case 3: Asymmetry Analysis
**Question:** Does left-side complexity affect right-side constituent size?

**Answer:** Compare in the same language:
- `Helix_English_en.tsv`: Row `V X X` (exact: 0 left, 2 right)
- `Helix_AnyOtherSide_English_en.tsv`: Row `... V X X` (any left, 2 right)

If sizes differ significantly, left side influences right side complexity.

### Use Case 4: Core Bilaterality
**Question:** What about verbs with dependencies on BOTH sides, ignoring totals?

**Answer:** Check the middle row `... X V X ...` in `Helix_AnyOtherSide_*.tsv`
- Shows all verbs with at least 1 left AND 1 right dependent
- Captures core bilateral verb behavior regardless of total complexity

---

## 7. Backward Compatibility

### What Stays the Same
- ✅ Exact configuration matching (VXX, XXV, XVXX) unchanged
- ✅ Standard Helix tables unchanged
- ✅ Existing HTML files unchanged
- ✅ All current analysis code works as before

### What's New
- ✅ Additional HTML files (partial configs)
- ✅ Additional Helix table files (marginal stats)
- ✅ New keys in position data (with `_anyright` / `_anyleft` suffix)

### Migration
- No migration needed - pure addition
- Old notebooks/scripts continue working
- New features opt-in via new filenames

---

## 8. Testing Strategy

### Test 1: Exact vs Partial Counts
```python
# For language with 100 VXX verbs (0 left, 2 right):
# - 30 have context XV (1 left added)
# - 20 have context XXV (2 left added)

Expected results:
- VXX exact count: 100
- VXX_anyleft count: 150 (100 + 30 + 20)
```

### Test 2: Statistics Consistency
```python
# VXX_anyleft should have:
# - Higher N (more examples)
# - Possibly different GM (includes more contexts)
# - Should NOT be wildly different (same right-side pattern)
```

### Test 3: No Double Counting
```python
# Verify XVXX contributes to:
# - XVXX (exact) ✓
# - VXX_anyleft ✓
# - XV_anyright ✓
# But NOT to:
# - VXX (exact) ✗
# - XXV (exact) ✗
```

---

## 9. Documentation Updates

Files to update:
- `docs/HTML_SAMPLE_VS_GLOBAL_INVESTIGATION.md` - Add section on partial configs
- `docs/HELIX_TABLE_METHODOLOGY.md` - Document marginal tables
- `docs/CONFIG_EXAMPLES_QUICKSTART.md` - Explain partial patterns
- `README.md` - Add marginal analysis to feature list

---

## 10. Open Questions

1. **Naming finalization**: Use `_anyleft/_anyright` or shorter alternative?
2. **Max examples**: Keep 10-20 per config or increase for partial configs?
3. **Table layout**: Same format as standard Helix or modified?
4. **Filtering**: Apply same MIN_COUNT threshold to marginal stats?

---

**Status**: Planning phase complete
**Next Step**: Review plan and begin Phase 1 implementation
**Estimated Effort**: 2-3 days for full implementation + testing
