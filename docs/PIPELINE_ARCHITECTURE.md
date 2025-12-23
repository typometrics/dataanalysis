# Pipeline Architecture & Module Dependencies

This document describes the current analysis pipeline architecture, module dependencies, and data flow.

## Summary

- **Total Notebooks**: 7 (numbered sequence)
- **Total Python Modules**: 20
- **Active Modules**: 15 (imported by notebooks)
- **Potentially Unused**: 5 (standalone or legacy)

## Notebook Module Dependencies

### 01_data_preparation_and_validation.ipynb
**Purpose**: Data loading, validation, and preprocessing  
**Imports**:
- ✓ `data_utils` - Google Sheets integration, metadata management
- ✓ `conll_processing` - Short file creation, CoNLL reading
- ✓ `validation` - Language code/group validation, statistics

**Key Operations**:
- Loads UD treebanks v2.17
- Validates language codes against Google Sheets
- Creates 10k sentence chunks (2.17_short/)
- Exports metadata.pkl for pipeline

---

### 02_dependency_analysis.ipynb
**Purpose**: Core metric computation (main computational bottleneck)  
**Imports**:
- ✓ `data_utils` - Load metadata
- ✓ `conll_processing` - Parallel dependency analysis (**primary workhorse**)
- ✓ `analysis` - Filtering, MAL computation

**Key Operations**:
- Calls `get_all_stats_parallel()` - unified processing of all metrics
- Computes dependency sizes, bastards, VO/HI, disorder (optional)
- Filters by MIN_COUNT threshold
- Saves 6+ pickle files

**Note**: Uses multiprocessing across ALL CPU cores

---

### 03_visualization.ipynb
**Purpose**: Interactive exploration of results  
**Imports**:
- ✓ `data_utils` - Load metadata
- ✓ `analysis` - Load analysis results
- ✓ `plotting` - MAL curves, heatmaps, scatter plots

**Key Operations**:
- Loads processed data from notebook 02
- Generates exploratory visualizations
- 2D/3D scatter plots, group statistics

---

### 04_data_processing.ipynb
**Purpose**: Factor computation and disorder analysis  
**Imports**:
- ✓ `data_utils` - Load metadata
- ✓ `compute_factors` - HCS, diagonal factors
- ✓ `verb_centered_analysis` - Table generation
- ✓ `compute_disorder` - Disorder statistics

**Key Operations**:
- Computes HCS (Hierarchical Complexity Scores)
- Generates verb-centered tables with growth factors
- Analyzes constituent ordering (disorder detection)
- Merges with head-initiality data

---

### 05_comparative_visualization.ipynb
**Purpose**: Comprehensive plot generation (batch mode)  
**Imports**:
- ✓ `data_utils` - Load metadata
- ✓ `plotting` - Batch plot generation (`plot_all()`)

**Key Operations**:
- Generates ~800 plots total (MAL, HCS, DIAG)
- Creates subsets: IE, non-IE, head-initial, head-final, VO, OV
- Uses multiprocessing (parallel=True)
- **Takes 8-15 minutes to complete**

---

### 06_factor_analysis.ipynb
**Purpose**: Correlation analysis and WALS validation  
**Imports**:
- ✓ `data_utils` - Load metadata
- ✓ `compute_factors` - Factor computation
- ✓ `plotting` - Scatter plots with regression

**Key Operations**:
- Analyzes factor correlations (HCS, diagonal factors vs. word order)
- Validates against WALS Feature 83A (OV/VO ordering)
- Statistical significance testing
- Downloads WALS data from clld.org

---

### 07_export_plots.ipynb
**Purpose**: Data packaging for distribution  
**Imports**: (Standard libraries only - os, subprocess)

**Key Operations**:
- Creates zip archives of plots/ and data/
- Excludes .pkl files from archives

---

## Module Classification

### ✅ Core Pipeline Modules (Actively Used)

1. **`data_utils.py`** - Used by notebooks 01-06
   - Google Sheets integration
   - Metadata serialization (save/load)
   - Language mappings

2. **`conll_processing.py`** - Used by notebooks 01-02 (CRITICAL)
   - Main computational engine
   - Parallel processing of all metrics
   - Functions: `get_all_stats_parallel()`, `make_shorter_conll_files()`, etc.

3. **`analysis.py`** - Used by notebooks 02-03
   - MAL computation
   - Position filtering
   - Average size calculation

4. **`validation.py`** - Used by notebook 01
   - Language code validation
   - Group validation
   - Basic statistics

5. **`conll.py`** - Used by `conll_processing.py`
   - Tree data structure
   - CoNLL-U parsing
   - Span computation (including bastards)

6. **`plotting.py`** - Used by notebooks 03, 05, 06
   - All visualization functions
   - Batch plot generation with parallelization
   - Label adjustment

7. **`compute_factors.py`** - Used by notebooks 04, 06
   - HCS factor computation
   - Diagonal factor computation
   - Dependency length ratios

8. **`compute_disorder.py`** - Used by notebook 04
   - Disorder detection
   - Percentage computation
   - DataFrame creation

9. **`verb_centered_analysis.py`** - Used by notebook 04
   - Table formatting
   - Growth factor display

10. **`adjustText.py`** - Used by `plotting.py`
    - 3rd-party library (modified)
    - Label positioning optimization

11. **`statConll_fast.py`** - Used by `validation.py`
    - Legacy validation functions
    - File discovery helpers
    - Language code checking

### ⚠️ Standalone/Utility Scripts (May Be Unused)

12. **`compute_vo_vs_hi.py`** - Standalone script
    - Computes VO/HI metrics independently
    - **Status**: Not imported by notebooks, but notebook 02 includes this functionality
    - **Reason**: May be for external/manual execution

13. **`compute_sentence_disorder.py`** - Alternative implementation
    - Sentence-level disorder computation
    - **Status**: Functionality integrated into `conll_processing.py`
    - **Reason**: Legacy or alternative approach

14. **`06_factor_analysis.py`** - Standalone Python script
    - **Status**: Duplicate of notebook 06
    - **Reason**: Likely for command-line execution
    - **Note**: Contains identical analysis code

15. **`find_de_files.py`** - Utility script
    - **Status**: Not imported anywhere
    - **Reason**: Likely for manual German treebank discovery

16. **`manage.py`** - Django management
    - **Status**: No Django project in workspace
    - **Reason**: Legacy from previous Django integration

### 🧪 Testing/Debugging Scripts (Not in Pipeline)

17. **`test_plot.py`** - Plot testing
18. **`test_dep_sizes_bastards.py`** - Unit tests
19. **`debug_bastard_examples.py`** - Bastard debugging
20. **`debug_exact.py`** - Exact computation verification
21. **`debug_user_example.py`** - User issue reproduction
22. **`reproduce_bastards.py`** - Bastard reproduction

**Status**: These are for development/debugging, not part of the pipeline

---

## Unused/Redundant Files Identified

### Definitely Unused
- `manage.py` - No Django in workspace
- `find_de_files.py` - Not imported, likely one-off utility

### Potentially Redundant (Duplicates)
- `compute_vo_vs_hi.py` - Functionality integrated in `conll_processing.py`
- `compute_sentence_disorder.py` - Functionality integrated in `conll_processing.py`
- `06_factor_analysis.py` - Duplicate of notebook 06

### Test/Debug (Not for Production)
- `test_plot.py`
- `test_dep_sizes_bastards.py`
- `debug_*.py` (3 files)
- `reproduce_bastards.py`

**Recommendation**: These could be moved to a `tests/` or `debug/` directory to declutter the main workspace.

---

## Data Flow Diagram

```
[UD Treebanks v2.17]
        ↓
[01] Data Preparation
    → metadata.pkl
    → 2.17_short/*.conllu
        ↓
[02] Dependency Analysis ← conll_processing.py (MAIN ENGINE)
    → all_langs_*.pkl (6 files)
    → vo_vs_hi_scores.csv
        ↓
        ├─→ [03] Visualization ← plotting.py
        │       → Interactive plots
        │
        ├─→ [04] Factor Computation ← compute_factors.py, compute_disorder.py
        │       → hcs_factors.csv
        │       → disorder statistics
        │       → verb_centered_table.txt
        │
        ├─→ [05] Comprehensive Plots ← plotting.py (batch mode)
        │       → plots/ (800+ files)
        │       → IE-plots/, noIE-plots/, etc.
        │
        ├─→ [06] Factor Analysis ← compute_factors.py
        │       → Correlation plots
        │       → WALS validation
        │
        └─→ [07] Export
                → plots_and_data.zip
```

---

## Performance Profile

| Stage | Notebook | Runtime | CPU Usage | Notes |
|-------|----------|---------|-----------|-------|
| Data Loading | 01 | 30-60s | Low | One-time setup |
| **Main Computation** | 02 | **40-90s** | **100% (all cores)** | Bottleneck |
| Exploration | 03 | <1 min | Low | Interactive |
| Factor Computation | 04 | 5-10s | Low | Fast |
| **Plot Generation** | 05 | **8-15 min** | **High** | ~800 plots |
| Analysis | 06 | 2-5 min | Low-Medium | WALS download + plots |
| Export | 07 | 30s | Low | ZIP creation |

**Total Pipeline Runtime**: ~15-25 minutes (with plot generation)  
**Without comprehensive plots (skip 05)**: ~2-5 minutes

---

## Module Complexity Ranking

| Module | Lines of Code | Complexity | Dependencies |
|--------|--------------|------------|--------------|
| `conll_processing.py` | ~1000 | ★★★★★ | conll.py |
| `plotting.py` | ~950 | ★★★★☆ | adjustText.py |
| `conll.py` | ~700 | ★★★★☆ | None |
| `statConll_fast.py` | ~550 | ★★★☆☆ | conll.py |
| `adjustText.py` | ~450 | ★★★☆☆ | None (3rd-party) |
| `analysis.py` | ~200 | ★★☆☆☆ | None |
| `compute_factors.py` | ~100 | ★★☆☆☆ | None |
| `verb_centered_analysis.py` | ~200 | ★★☆☆☆ | None |
| `compute_disorder.py` | ~150 | ★★☆☆☆ | None |
| `data_utils.py` | ~200 | ★★☆☆☆ | gspread |
| `validation.py` | ~150 | ★★☆☆☆ | statConll_fast.py |

**Most Complex/Critical**: `conll_processing.py` - handles all tree traversal and metric computation

---

## Recommendations

### For Code Organization
1. **Move test/debug files** to `tests/` subdirectory
2. **Archive redundant files** (compute_vo_vs_hi.py, etc.) to `old/` or document their standalone purpose
3. **Consider consolidating** `compute_sentence_disorder.py` functionality (already in conll_processing.py)

### For Performance
1. **Notebook 02**: Consider checkpointing to allow resuming if interrupted
2. **Notebook 05**: Add option to generate subset of plots (e.g., skip regplots)
3. **General**: Cache expensive operations (already done with pickle files)

### For Maintenance
1. **Add unit tests** for core functions in `conll_processing.py`
2. **Document** the standalone script usage (if intentional)
3. **Version control** for data files (consider DVC for large pickle files)

---

## Conclusion

The pipeline is well-structured with clear separation of concerns:
- **Data loading**: 01
- **Computation**: 02 (main workhorse)
- **Exploration**: 03
- **Advanced metrics**: 04
- **Publication-ready plots**: 05
- **Analysis**: 06
- **Export**: 07

The core computational logic is concentrated in `conll_processing.py`, which is efficiently parallelized. The visualization layer (`plotting.py`) is modular and supports batch generation.

**Main areas for cleanup**: Test files and potentially redundant standalone scripts. These don't impact the pipeline but could be organized better for clarity.
