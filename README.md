# Typometrics Data Analysis Pipeline

A comprehensive analysis pipeline for extracting and visualizing typometric patterns from Universal Dependencies treebanks, focusing on verb-centered dependency structures, constituent ordering, and cross-linguistic variation.

## Overview

This pipeline processes Universal Dependencies treebanks to compute linguistic metrics including:
- **Dependency sizes and positions** - Distance patterns of verbal dependents
- **Mean Aggregate Length (MAL)** - Average dependency lengths for n-ary branching
- **Head-Initiality & VO ordering** - Word order typology indicators  
- **Hierarchical Complexity Score (HCS)** - Growth factors between adjacent positions
- **Constituent disorder** - Violations of monotonic ordering patterns
- **Bastard dependencies** - Discontinuous dependency structures
- **AnyOtherSide patterns** - Partial configurations ignoring one direction

## Analysis Pipeline

### Notebooks (Run in Sequence)

**1. `01_data_preparation_and_validation.ipynb`** - Data Loading & Validation
   - Loads UD treebanks v2.17 CoNLL-U files
   - Validates language codes and family groups via Google Sheets integration
   - Creates short CoNLL files (10k sentence chunks) for parallel processing
   - Computes basic corpus statistics (files, sentences, tokens)
   - Exports metadata for downstream notebooks

**2. `02_dependency_analysis.ipynb`** - Core Metrics Computation
   - Parallel processing of dependency sizes across all treebanks
   - Computes dependency position statistics for verb-centered constructions
   - Calculates VO scores and head-initiality metrics
   - Extracts bastard dependency statistics
   - Optional sentence-level disorder analysis
   - Filters results by minimum occurrence thresholds
   - Exports processed data to pickle files

**3. `03_visualization.ipynb`** - Exploratory Visualization
   - Interactive plots of MAL curves (n=2,3,5)
   - Heatmaps of dependency patterns across languages
   - 2D/3D scatter plots of MAL relationships
   - Position distribution analysis (left_1, right_1, etc.)
   - Group-level statistical summaries

**4. `04_data_processing.ipynb`** - Factor Computation
   - Computes HCS (Hierarchical Complexity Score) factors
   - Generates diagonal growth factors (cross-position comparisons)
   - Creates verb-centered constituent size tables (standard and AnyOtherSide)
   - Analyzes constituent disorder patterns (ordered vs. disordered)
   - Merges with head-initiality data
   - Generates configuration example HTML visualizations

**5. `05_comparative_visualization.ipynb`** - Comprehensive Plotting
   - Generates ~200+ scatter plots (MAL, HCS, DIAG types)
   - Creates language subset plots (IE, non-IE, head-initial, head-final, VO, OV)
   - Produces regression plots for all combinations
   - Uses parallel processing for efficient batch generation
   - Archives results as zip files

**6. `06_factor_analysis.ipynb`** - Correlation Analysis
   - Analyzes relationships between linguistic factors
   - Head-initiality vs. VO score correlations
   - Diagonal factors vs. word order typology
   - Disorder patterns vs. head-initiality
   - WALS validation (Feature 83A: Basic Word Order)
   - Statistical significance testing

**7. `07_export_plots.ipynb`** - Data Export
   - Creates zip archives of plots and data
   - Prepares results for publication/sharing

## Core Python Modules

### Data Processing

**`data_utils.py`** - Metadata & Configuration Management
- `load_google_sheets()` - Loads language metadata from Google Sheets
- `create_language_mappings()` - Maps language codes to names and groups
- `save_metadata()` / `load_metadata()` - Pickle serialization for pipeline state

**`corpus_prep.py`** - Corpus Preparation
- `make_shorter_conll_files()` - Splits large files into 10k sentence chunks
- `read_shorter_conll_files()` - Reads processed chunks

**`conll_processing.py`** - CoNLL-U File Processing (Main Workhorse)
- `get_dep_sizes()` - Extracts dependency sizes from tree structures (exact and anyother configurations)
- `process_kids()` - Records position statistics including `_anyother` and `_anyother_totright_N`/`_anyother_totleft_N` keys
- `get_all_stats_parallel()` - Unified parallel processing (dependencies, VO/HI, bastards, disorder)
- `extract_verb_config_examples()` - Collects example sentences for configurations (exact and partial)
- `get_bastard_stats()` - Identifies discontinuous dependencies
- `get_vo_hi_stats()` - Computes verb-object and head-initiality metrics
- `get_sentence_disorder()` - Checks for disordered constituent patterns

**`validation.py`** - Data Validation
- `validate_language_codes()` - Checks ISO 639-3 codes against Google Sheets
- `validate_language_groups()` - Verifies language family assignments
- `compute_basic_statistics()` - Corpus size statistics (files, sentences, tokens)

**`conll.py`** - Tree Structure Utilities
- `Tree` class - Core dependency tree data structure
- `conllFile2trees()` - Parser for CoNLL-U format
- `addspan()` - Computes constituent spans (linear and with bastards)

### Analysis & Computation

**`analysis.py`** - Statistical Analysis
- `filter_by_min_count()` - Removes low-frequency positions
- `compute_MAL_per_language()` - Calculates Mean Aggregate Length
- `compute_average_sizes()` - Position-wise average dependency sizes
- `save_analysis_results()` / `load_analysis_results()` - Pipeline state management

**`compute_factors.py`** - Linguistic Factors
- `compute_hcs_factors()` - Hierarchical Complexity Scores (adjacent position ratios)
- `compute_diagonal_factors()` - Cross-position growth factors
- `compute_dep_length_ratios()` - Dependency length ratios

**`compute_disorder.py`** - Constituent Ordering
- `compute_disorder_per_language()` - Detects non-monotonic size sequences
- `compute_disorder_percentages()` - Aggregates disorder statistics
- `compute_disorder_statistics()` - Full disorder analysis pipeline

**`verb_centered_analysis.py`** - Verb-Centered Tables (Wrapper)
- `create_verb_centered_table()` - Unified entry point for table creation
- `compute_average_sizes_table()` - Aggregates exact configuration statistics
- `compute_anyotherside_sizes_table()` - Aggregates partial configuration statistics (with tot dimension for diagonal factors)
- `generate_mass_tables()` - Generates all table variants (global, individual, family, order, anyotherside)
- `generate_anyotherside_helix_tables()` - Generates AnyOtherSide tables with horizontal and diagonal growth factors (TSV/XLSX)
- `build_anyotherside_table_structure()` - Creates table structure with factor rows for partial configurations
- `format_verb_centered_table()` - Formats tables as text/TSV
- `extract_verb_centered_grid()` - Extracts grid structure
- *Note: Uses `verb_centered_model`, `verb_centered_builder`, and `verb_centered_formatters` internally.*

**`generate_html_examples.py`** - Configuration Example Visualizations
- `generate_all_html()` - Creates HTML files from collected examples
- `classify_configuration()` - Determines config type (exact, partial_left, partial_right, partial_both)
- `calculate_position_stats()` - Computes statistics with conditional display for partial configs

### Visualization

**`plotting.py`** - Comprehensive Plotting Functions
- `plot_mal_curves_with_groups()` - MAL curves colored by language family
- `plot_scatter_2d()` - 2D scatter plots with regression lines and labels
- `plot_dependency_sizes()` - Scatter plots comparing two dependency positions
- `plot_hcs_factor()` - Hierarchical complexity score visualizations
- `plot_head_initiality_vs_factors()` - Factor correlations with word order
- `plot_all()` - Batch generation of all plot types (parallelized)
- `adjust_text_labels()` - Label placement optimization (uses adjustText.py)

**`adjustText.py`** - Label Positioning (3rd-party, modified)
- Optimizes text label placement to avoid overlaps in scatter plots

### Standalone Analysis Scripts

**`compute_vo_vs_hi.py`** - VO/Head-Initiality Computation
- Standalone script to compute word order metrics from CoNLL files
- Exports results to CSV

**`compute_sentence_disorder.py`** - Sentence-Level Disorder
- Alternative disorder computation at sentence level (vs. average level)

**`statConll_fast.py`** - Legacy Fast Processing
- Original fast validation functions (used by `validation.py`)
- `getAllConllFiles()` - File discovery
- `checkLangCode()` / `checkLangGroups()` - Validation helpers

### Debugging & Testing
(Moved to `debug/` directory)

### Unused/Legacy Files

Based on recent cleanup:
- `find_de_files.py` - (Removed)
- `manage.py` - (Removed)
- `test_plot.py` - (Removed)
- `06_factor_analysis.py` - (Removed)

## Data Files & Directories

### Input Data
- **`ud-treebanks-v2.17/`** - Universal Dependencies treebanks (download separately)
- **`sud-treebanks-v2.17/`** - Surface-Syntactic Universal Dependencies (if used)
- **`excluded_treebanks.txt`** - List of treebanks to exclude from analysis
- **`languageCodes.tsv`** - ISO 639-3 language code mappings

### Documentation (`docs/`)
- **[Documentation Overview](docs/README.md)** - Central index for all project documentation.
- `PLOT_DOCUMENTATION.md` - Guide to plots and visualizations.
- `HELIX_TABLE_METHODOLOGY.md` - Detailed methodology.
- `HELIX_TABLE_USER_GUIDE.md` - User-facing guide.
- ...see `docs/README.md` for full list.

### Intermediate Data (Generated by Pipeline)
- **`2.17_short/`** - Short CoNLL files (10k sentence chunks) for parallel processing
- **`data/`** - Cached analysis results
  - `metadata.pkl` - Language mappings and configuration
  - `all_langs_position2num.pkl` - Occurrence counts per position
  - `all_langs_position2sizes.pkl` - Raw size distributions
  - `all_langs_average_sizes.pkl` - Average sizes per position (exact and anyother)
  - `all_config_examples.pkl` - Configuration examples (exact and partial)
  - `lang2MAL.pkl` - Mean Aggregate Length per language
  - `vo_vs_hi_scores.csv` - VO and head-initiality scores
  - `hcs_factors.csv` - Hierarchical Complexity Scores
  - `sentence_disorder_percentages.csv` / `.pkl` - Sentence-level disorder data
  - `verb_centered_table.txt` / `.csv` - Verb-centered constituent tables
  - `tables/` - Generated Helix tables (standard and AnyOtherSide, TSV/XLSX)


### Output Data
- **`plots/`** - Main visualization output (scatter plots, MAL, HCS, DIAG)
- **`html_examples/`** - Interactive configuration example visualizations
  - Organized by language with index page
  - Exact configs (VXX, XXV) and partial configs (VXX_anyleft, XXV_anyright, XVX_anyboth)
- **`regplots/`** - Regression plot variants
- **`IE-plots/`, `IE-regplots/`** - Indo-European language subset
- **`noIE-plots/`, `noIE-regplots/`** - Non-Indo-European subset
- **`headInit-plots/`, `headFinal-plots/`** - Head-initial/final subsets
- **`VO-plots/`, `OV-plots/`** - Verb-object ordering subsets
- **`*.zip`** - Archived plot collections
- **`*.png`** - Individual analysis figures (disorder, factors, WALS validation)

### Configuration
- **`typometrics-c4750cac2e21.json`** - Google Sheets API credentials (gitignored)
- **`typometrics-c4750cac2e21.json.template`** - Credentials template

## Detailed Module Analysis

### Notebook-to-Module Dependencies

| Notebook | Imported Modules | Key Functions Used |
|----------|-----------------|-------------------|
| **01_data_preparation_and_validation.ipynb** | `data_utils`, `conll_processing`, `validation` | `load_google_sheets()`, `create_language_mappings()`, `validate_language_codes()`, `validate_language_groups()`, `make_shorter_conll_files()`, `compute_basic_statistics()` |
| **02_dependency_analysis.ipynb** | `data_utils`, `conll_processing`, `analysis` | `load_metadata()`, `get_all_stats_parallel()`, `filter_by_min_count()`, `compute_MAL_per_language()`, `save_analysis_results()` |
| **03_visualization.ipynb** | `data_utils`, `analysis`, `plotting` | `load_metadata()`, `load_analysis_results()`, `plot_mal_curves_with_groups()`, `plot_mal_heatmap()`, `plot_scatter_2d()`, `plot_scatter_3d()` |
| **04_data_processing.ipynb** | `data_utils`, `compute_factors`, `verb_centered_analysis`, `compute_disorder` | `load_metadata()`, `compute_hcs_factors()`, `compute_average_sizes_table()`, `format_verb_centered_table()`, `compute_disorder_statistics()` |
| **05_comparative_visualization.ipynb** | `data_utils`, `plotting` | `load_metadata()`, `plot_all()`, `plot_head_initiality_vs_factors()`, `plot_dependency_sizes()` |
| **06_factor_analysis.ipynb** | `data_utils`, `compute_factors`, `plotting` | `load_metadata()`, `compute_hcs_factors()`, `plot_scatter_2d()`, WALS data integration |
| **07_export_plots.ipynb** | (Standard libraries) | ZIP archive creation |

### Module Dependency Graph

```
conll.py (Tree structure)
    ↓
conll_processing.py (uses conll.py)
    ↓
├─→ analysis.py (computes MAL, averages)
├─→ compute_factors.py (computes HCS, diagonal factors)
├─→ compute_disorder.py (disorder analysis)
├─→ verb_centered_analysis.py (table formatting)
└─→ plotting.py (visualization)
    ↑
data_utils.py ─────────────┘ (metadata management)
validation.py (uses statConll_fast.py)
```

### Key Function Reference

#### Data Loading & Preparation
- `conll.conllFile2trees(path)` - Parse CoNLL-U file to tree objects
- `conll.Tree.addspan()` - Compute constituent spans (with/without bastards)
- `conll_processing.make_shorter_conll_files()` - Split into 10k chunks
- `data_utils.load_google_sheets()` - Load language metadata from Google Sheets

#### Core Analysis
- `conll_processing.get_all_stats_parallel()` - **Master function**: Computes ALL metrics in parallel
  - Dependencies: position2num, position2sizes, average_sizes
  - Bastards: verb counts, bastard counts, relation distributions
  - VO/HI: verb-object ordering, head-initiality scores
  - Disorder: sentence-level disorder flags (optional)
- `analysis.compute_MAL_per_language()` - Mean Aggregate Length calculation
- `analysis.filter_by_min_count()` - Remove low-frequency positions

#### Factor Computation
- `compute_factors.compute_hcs_factors()` - Ratios between adjacent positions
  - Example: `right_2_totright_3 / right_1_totright_3` (HCS factor)
- `compute_factors.compute_diagonal_factors()` - Cross-position ratios
  - Example: `right_2_totright_2 / left_2_totleft_2` (asymmetry)
- `compute_disorder.compute_disorder_statistics()` - Detect non-monotonic ordering

#### Visualization
- `plotting.plot_all()` - **Batch generator**: Creates ~70 plots per subset
  - Generates MAL, HCS, and DIAG scatter plots
  - Uses multiprocessing for parallelization
  - Supports language filtering (IE, non-IE, VO, OV, etc.)
- `plotting.plot_dependency_sizes()` - Individual scatter plot with regression
- `plotting.plot_mal_curves_with_groups()` - MAL curves colored by family

### Performance Characteristics

| Operation | Typical Runtime | Parallelization | Notes |
|-----------|----------------|-----------------|-------|
| Short file creation (01) | 30-60 sec | No | One-time setup |
| Dependency analysis (02) | 40-90 sec | Yes (all cores) | Main bottleneck |
| Factor computation (04) | 5-10 sec | No | Fast |
| Plot generation (05) | 8-15 min | Yes (4-8 workers) | ~800 plots total |
| Sentence disorder (02 optional) | +30-60 sec | Yes | Adds to analysis time |

## Setup & Installation

### Requirements

```bash
pip install pandas numpy matplotlib seaborn scipy tqdm gspread oauth2client
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

### Google Sheets Configuration

The project uses Google Sheets API for language metadata management.

**Setup Steps:**
1. Create a Google Cloud project at https://console.cloud.google.com/
2. Enable Google Sheets API
3. Create a service account and download credentials JSON
4. Copy `typometrics-c4750cac2e21.json.template` to `typometrics-c4750cac2e21.json`
5. Paste your credentials into the JSON file

**Google Sheets Structure:**

The spreadsheet should contain these worksheets:
- **my_language** - Custom display names for languages (overrides ISO names)
- **language_to_group** - Language family/genus assignments
- **appearance** - Color codes for language groups (for plots)
- **all_languages_code** - ISO 639-3 codes and standard names

**Spreadsheet URL** (default): `https://docs.google.com/spreadsheets/d/1IP3ebsNNVAsQ5sxmBnfEAmZc4f0iotAL9hd4aqOOcEg/edit`

## Usage

### Quick Start

```bash
# 1. Download UD treebanks (manual step)
# Visit: https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-5772
# Extract to: ud-treebanks-v2.17/

# 2. Configure Google Sheets credentials (see Setup section)

# 3. Run notebooks in sequence
jupyter notebook
# Then open and run: 01, 02, 03, 04, 05, 06, 07
```

### Running Individual Notebooks

```python
# Notebook 01: Data Preparation (Required first)
# Creates metadata.pkl and 2.17_short/ directory

# Notebook 02: Analysis (Main computation)
# Set compute_sentence_disorder = True/False
# Outputs: 6 pickle files + VO/HI scores

# Notebook 03: Quick visualization
# Explore results interactively

# Notebook 04: Factor computation
# Computes HCS, diagonal factors, disorder

# Notebook 05: Comprehensive plots
# Warning: Takes 8-15 minutes, generates 800+ plots
# Use parallel=True for speed

# Notebook 06: Correlation analysis
# Includes WALS validation

# Notebook 07: Export
# Creates zip archives
```

### Customization

**Filter languages:**
```python
# In notebook 05
indo_euro_langs = {l for l in langs if langnameGroup.get(l) == 'Indo-European'}
plotting.plot_all(data, langNames, langnameGroup, filter_lang=indo_euro_langs, ...)
```

**Adjust minimum occurrence threshold:**
```python
# In notebook 02
MIN_COUNT = 10  # Default: 10, increase for stricter filtering
```

**Enable sentence-level disorder:**
```python
# In notebook 02
compute_sentence_disorder = True  # Default: True
```

## Plot Types & Naming Conventions

### Plot Categories

1. **MAL Plots** (Mean Average Length)
   - Format: `right pos 1 tot 1 vs tot 2 MAL.png`
   - Compares same position across different total contexts
   - Example: Right position 1 in "V X" vs "V X X" configurations

2. **HCS Plots** (Hierarchical Complexity Score)
   - Format: `right tot 2 pos 1 vs pos 2 HCS.png`
   - Compares adjacent positions within same total context
   - Shows growth factors between consecutive positions

3. **DIAG Plots** (Diagonal Comparisons)
   - Format: `right pos 1 tot 1 vs pos 2 tot 2 DIAG.png`
   - Compares different positions in different contexts
   - Reveals asymmetric growth patterns

4. **Regression Plots**
   - Add " regplot" suffix to any plot name
   - Example: `right pos 1 tot 1 vs tot 2 MAL regplot.png`

### Position Naming Convention

- **Direction**: `left` or `right` (from verb)
- **Position**: `pos 1`, `pos 2`, `pos 3`, ... (distance from verb)
- **Total**: `tot 2`, `tot 3`, `tot 4`, ... (total number of dependents on that side)

**Examples:**
- `right_1_totright_2` = First right dependent when verb has 2 right dependents
- `left_3_totleft_4` = Third left dependent when verb has 4 left dependents

## Language Direction & Numbering

**Right dependents (postverbal):**
- Numbered 1, 2, 3, ... from verb outward (V → X₁ X₂ X₃)
- Typical in VO languages

**Left dependents (preverbal):**
- Also numbered 1, 2, 3, ... from verb outward (X₃ X₂ X₁ ← V)
- Note: Internal processing reverses indices for consistency
- Typical in OV languages

## Output Examples

### Generated Data Files

```
data/
├── metadata.pkl                          # Pipeline state
├── all_langs_position2num.pkl           # Occurrence counts
├── all_langs_average_sizes.pkl          # Filtered average sizes
├── lang2MAL.pkl                         # MAL per language
├── vo_vs_hi_scores.csv                  # Word order metrics
├── hcs_factors.csv                      # Complexity scores
├── sentence_disorder_percentages.csv    # Disorder statistics
└── verb_centered_table.txt              # ASCII table
```

### Generated Plots (Example)

```
plots/
├── right pos 1 tot 1 vs tot 2 MAL.png
├── right pos 1 tot 1 vs tot 2 MAL regplot.png
├── right tot 2 pos 1 vs pos 2 HCS.png
└── right pos 1 tot 1 vs pos 2 tot 2 DIAG.png

IE-plots/                                 # Indo-European subset
noIE-plots/                               # Non-Indo-European subset
headInit-plots/                           # Head-initial languages
headFinal-plots/                          # Head-final languages
VO-plots/                                 # Verb-Object languages
OV-plots/                                 # Object-Verb languages
```

## Troubleshooting

### Common Issues

**1. Google Sheets API Error**
```
Error: Credentials not found
Solution: Copy typometrics-c4750cac2e21.json.template to .json and add credentials
```

**2. UD Treebanks Not Found**
```
Error: ud-treebanks-v2.17/ not found
Solution: Download from https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-5772
```

**3. Notebook 02 Takes Too Long**
```
Issue: Dependency analysis running >5 minutes
Solution: Check CPU count (uses all cores), reduce treebank size, or disable sentence disorder
```

**4. Out of Memory During Plot Generation**
```
Issue: Memory error in notebook 05
Solution: Reduce parallel workers (set parallel=False or use fewer workers in multiprocessing)
```

**5. Missing Sentence Disorder Data**
```
Error: sentence_disorder_percentages.csv not found (notebook 04)
Solution: Re-run notebook 02 with compute_sentence_disorder=True
```

## Advanced Usage

### Computing Custom Metrics

Add custom metrics to `conll_processing.get_all_stats_parallel()`:

```python
# In conll_processing.py
def process_file_complete(conll_filename, ...):
    # Add your metric computation here
    custom_metric = compute_my_metric(tree)
    return (..., custom_metric)
```

### Creating Custom Plots

```python
# In plotting.py or in a notebook
def plot_my_analysis(data, ...):
    fig, ax = plt.subplots(figsize=(12, 8))
    # Your plotting code
    plt.savefig('my_analysis.png')
```

### Filtering Languages by Custom Criteria

```python
# Example: Languages with >50k sentences
large_langs = {l for l, files in langConllFiles.items() 
               if sum(count_sentences(f) for f in files) > 50000}

plotting.plot_all(data, langNames, langnameGroup, 
                  filter_lang=large_langs, 
                  folderprefix='large-')
```

## Citation

If you use this pipeline in your research, please cite:

```
[Add citation information here]
```

## Contributing

When making changes:
1. Keep notebooks modular and well-documented
2. Update module docstrings for new functions
3. Test with a small dataset first (use `excluded_treebanks.txt`)
4. Update this README if adding new features
5. Add new dependencies to `requirements.txt`

## License

[Add license information]

## References

- **Universal Dependencies**: https://universaldependencies.org/
- **UD v2.17 Release**: https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-5772
- **WALS Online**: https://wals.info/ (Feature 83A: Order of Object and Verb)
- **Google Sheets API**: https://developers.google.com/sheets/api
