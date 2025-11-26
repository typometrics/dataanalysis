# Typometrics Data Preparation

This repository contains the data preparation and analysis pipeline for typometric analysis of Universal Dependencies treebanks.

## Project Structure

### Core Modules (Python)

- **`data_utils.py`** - Google Sheets integration and metadata management
- **`conll_processing.py`** - CoNLL-U file processing and dependency analysis
- **`analysis.py`** - Statistical filtering and MAL computation
- **`validation.py`** - Language code and group validation
- **`plotting.py`** - Visualization functions
- **`conll.py`** - CoNLL-U tree structure utilities
- **`statConll_fast.py`** - Fast validation functions

### Analysis Notebooks (Jupyter)

Run these notebooks **in sequence**:

1. **`01_data_preparation_and_validation.ipynb`**
   - Load Universal Dependencies treebanks (v2.17)
   - Validate language codes and groups
   - Create short CoNLL files (10k sentence chunks)
   - Export metadata for subsequent notebooks

2. **`02_dependency_analysis.ipynb`**
   - Compute dependency metrics (parallel processing)
   - Calculate Mean Aggregate Length (MAL)
   - Filter by minimum occurrence counts
   - Export analysis results (6 pickle files)

3. **`03_visualization.ipynb`**
   - Interactive exploration of results
   - MAL curves, heatmaps, scatter plots
   - Position distributions
   - Group statistics

4. **`04_comparative_scatterplots.ipynb`**
   - Generate comparative scatter plots (MAL, HCS, DIAG)
   - Parallel plot generation
   - Creates plots for all languages, IE-only, and non-IE
   - Archives results as zip files

### Data Directories

- **`data/`** - Cached analysis results (pickle files)
- **`ud-treebanks-v2.17/`** - Universal Dependencies treebanks
- **`plots/`, `regplots/`** - Generated visualizations
- **`IE-plots/`, `IE-regplots/`** - Indo-European specific plots
- **`noIE-plots/`, `noIE-regplots/`** - Non-Indo-European plots
- **`old/`** - Archived legacy files

## Setup

### Requirements

```bash
pip install pandas numpy matplotlib seaborn scipy tqdm gspread oauth2client
```

### Google Sheets Credentials

The project uses Google Sheets API for language metadata. You need to:

1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create a service account and download credentials JSON
4. Copy `typometrics-c4750cac2e21.json.template` to `typometrics-c4750cac2e21.json`
5. Fill in your actual credentials

**Important:** The credentials file is in `.gitignore` and will NOT be committed to git.

### Google Sheets Structure

The spreadsheet should have 4 worksheets:
- **my_language** - Custom display names for languages (with spaces)
- **language_to_group** - Language family/genus assignments
- **appearance** - Color codes for language groups
- **all_languages_code** - ISO 639-3 codes and standard names

## Usage

### Quick Start

```bash
# Run notebooks in sequence
jupyter notebook 01_data_preparation_and_validation.ipynb
jupyter notebook 02_dependency_analysis.ipynb
jupyter notebook 03_visualization.ipynb
jupyter notebook 04_comparative_scatterplots.ipynb
```

### Cleanup

```bash
# Move unused files to old/ directory
chmod +x cleanup.sh
./cleanup.sh
```

## Plot Naming Conventions

Generated plots follow these patterns:

- **MAL**: `right pos 1 tot 1 vs tot 2 MAL.png`
  - Compares same position with different total contexts
  
- **HCS**: `right tot 2 pos 1 vs pos 2 HCS.png`
  - Hierarchical Complexity Scores (adjacent positions)
  
- **DIAG**: `right pos 1 tot 1 vs pos 2 tot 2 DIAG.png`
  - Diagonal comparisons (different positions and contexts)

Regression plots add " regplot" suffix.

## Performance

- **Parallel Processing**: Notebook 02 uses all CPU cores for dependency analysis
- **Plot Generation**: Notebook 04 uses multiprocessing for parallel plot creation
- **Progress Tracking**: tqdm progress bars for long-running operations

## Language Direction

- **Right dependents**: Numbered 1, 2, 3, ... from verb outward (→)
- **Left dependents**: Also numbered 1, 2, 3, ... from verb outward (←)
  - Note: Internal numbering is reversed to maintain consistency

## Legacy Components

The `old/` directory contains:
- Original monolithic notebook (`datapreparation.ipynb`)
- Legacy Python scripts
- Archived data files

## Django Integration

The Django components (`djangotypo/`, `typometricsapp/`) are for the web interface:
- Backend API for serving analysis results
- URL routing and views
- TSV to JSON conversion for frontend

See separate Django documentation for web interface setup.

## Contributing

When making changes:
1. Keep notebooks modular and focused
2. Update module docstrings
3. Test with a small dataset first
4. Update this README if adding new features

## License

[Add license information]
