# Verb Configuration Examples - Quick Start Guide

## Overview

Configuration examples are now collected **automatically** during the main data extraction process, ensuring they use the same constraints as constituent size computation (same dependency relations, bastard inclusion, etc.).

## Workflow

### Step 1: Extract Data (Collect Examples)

Run the main data extraction script:

```bash
python3 run_data_extraction.py
```

This will:
- Process all CoNLL files
- Compute all metrics (sizes, VO/HI, disorder, etc.)
- **Collect configuration examples** (up to 10 per configuration per language)
- Save examples to `data/all_config_examples.pkl`

**Time**: ~10-15 minutes on 80 cores for all 185+ languages

### Step 2: Generate HTML Visualizations

Generate interactive HTML files from the collected examples:

```bash
python3 generate_html_examples.py
```

This will:
- Load examples from `data/all_config_examples.pkl`
- Generate HTML files for each configuration per language
- Create an organized index page with navigation

**Time**: ~2-3 seconds

**Output**: `html_examples/` directory with structure:
```
html_examples/
  index.html                    # Main navigation page
  Abkhaz_ab/
    V_X.html
    V_X_X.html
    X_X_V.html
    ...
  English_en/
    V_X.html
    ...
```

### Step 3: View Results

Open the index page in a browser:

```bash
xdg-open html_examples/index.html
# or
firefox html_examples/index.html
```

The index page features:
- **Quick Access by Language**: Click language codes at the top to jump directly to that language
- **Quick Navigation by Type**: Navigate to left-branching only, right-branching only, or both
- **Three-Column Layout**: Languages organized by their branching patterns

Click on any configuration to see interactive dependency trees with:
- **Red highlighting**: Verb nodes (using MISC.highlight=red)
- **Green highlighting**: Dependent nodes (using MISC.highlight=green)
- **Interactive visualization**: Using reactive-dep-tree with proper CoNLL-U format

### Configuration Types

The generated HTML includes both **exact** and **partial** configurations:

**Exact Configurations** (e.g., `V_X_X.html`):
- Match specific left and right dependent counts
- Example: VXX = 0 left, 2 right dependents

**Partial Configurations** (e.g., `V_X_X_anyleft.html`):
- Match one side exactly while ignoring the other
- Three types:
  - **anyleft** (e.g., `VXX_anyleft`): 2 right dependents, any left dependents
    - HTML shows **only right side** constituents
  - **anyright** (e.g., `XXV_anyright`): 2 left dependents, any right dependents
    - HTML shows **only left side** constituents
  - **anyboth** (e.g., `XVX_anyboth`): 1 dependent each side, any totals
    - HTML shows **both sides**

This provides a more complete view of language patterns where one direction's structure matters independently of the other.

## Testing

Test the integration with a small subset:

```bash
python3 test_config_integration.py    # Test example collection
python3 test_html_generation.py       # Test HTML generation
```

## Configuration

### Modify Example Collection

Edit `run_data_extraction.py`:

```python
# Disable example collection
collect_config_examples = False

# Change number of examples per configuration
max_examples_per_config=10  # Default: 10
```

### Customize HTML Output

Edit `generate_html_examples.py` to modify:
- Styling (CSS in `generate_language_html()`)
- Layout (HTML structure)
- Colors for verb/dependent highlighting

## Features

### ✅ Guaranteed Consistency
- Examples collected **during** constituent size computation
- Uses **same** dependency relation filters
- Respects `include_bastards` flag
- No duplicate CoNLL file parsing

### ✅ Efficient Processing
- Parallel processing (80 cores)
- Minimal memory overhead (~10 examples per config)
- Fast HTML regeneration (no re-parsing needed)

### ✅ Organized Output
- Folder names match table conventions (e.g., `Abkhaz_ab`)
- Configurations sorted and categorized
- Quick navigation with 3-column layout
- Responsive design

## Data Format

### Configuration Examples Structure

```python
all_config_examples = {
    'ab': {  # Language code (base, not treebank)
        'V X X': [  # Configuration string
            {
                'tree': {
                    'forms': ['говорит', 'он', 'что-то'],
                    'upos': ['VERB', 'PRON', 'PRON'],
                    'heads': [0, 1, 1],
                    'deprels': ['root', 'nsubj', 'obj']
                },
                'verb_id': 1,  # 1-based index of verb
                'dep_ids': [2, 3]  # 1-based indices of dependents
            },
            # ... up to 10 examples
        ],
        # ... more configurations
    },
    # ... more languages
}
```

## Troubleshooting

### "File not found: all_config_examples.pkl"

Run `python3 run_data_extraction.py` first to collect examples.

### "No module named 'conll_processing'"

Make sure you're in the correct directory:
```bash
cd /bigstorage/kim/typometrics/dataanalysis
```

### Examples look wrong

The examples use the **same constraints** as constituent size computation:
- Only VERB governors
- Only specific relations: nsubj, obj, iobj, csubj, ccomp, xcomp, obl, expl, dislocated, advcl, advmod, nmod, appos, nummod, acl, amod
- Includes bastard dependents if `include_bastards=True`

If you want different examples, modify the constraints in both:
1. `extract_verb_config_examples()` in `conll_processing.py`
2. `get_dep_sizes()` in `conll_processing.py` (to keep them in sync)

### HTML shows garbled text

Make sure files are saved with UTF-8 encoding. The HTML generation uses:
```python
with open(output_file, 'w', encoding='utf-8') as f:
```

## Advanced Usage

### Extract Only Specific Languages

Modify `run_data_extraction.py`:

```python
# Filter to specific languages before processing
test_langs = {'en', 'fr', 'de'}  # English, French, German only
allshortconll = [
    f for f in allshortconll 
    if any(f.startswith(f'2.17_short/{lang}_') for lang in test_langs)
]
```

### Generate HTML for Subset

```python
from generate_html_examples import generate_all_html, load_config_examples

# Load all examples
examples = load_config_examples('data')

# Filter to specific languages
filtered = {k: v for k, v in examples.items() if k in {'en', 'fr', 'de'}}

# Save filtered version
import pickle
with open('data/filtered_examples.pkl', 'wb') as f:
    pickle.dump(filtered, f)

# Generate HTML from filtered
# (modify generate_all_html to use filtered file)
```

### Custom Example Selection

To implement smarter example selection (e.g., prefer shorter sentences), modify the collection logic in `process_file_complete()`:

```python
# Instead of first-come-first-served:
if len(config_examples[config]) < max_examples_per_config:
    config_examples[config].append(example)

# Sort by sentence length and keep shortest:
config_examples[config].append(example)
config_examples[config].sort(key=lambda x: len(x['tree']['forms']))
config_examples[config] = config_examples[config][:max_examples_per_config]
```

## Technical Implementation

### Core Processing (`conll_processing.py`)

#### `extract_verb_config_examples(tree, include_bastards=False)`
Extracts configuration string from a verb tree using the same constraints as `get_dep_sizes()`:
- Only processes VERB governors
- Uses same dependency relation filters (nsubj, obj, iobj, csubj, ccomp, xcomp, obl, expl, dislocated, advcl, advmod, nmod, appos, nummod, acl, amod)
- Respects bastard inclusion flag consistently
- Returns configuration string (e.g., "V X X" or "X X X V")

#### `process_file_complete()`
Modified to collect examples during normal processing:
- **New parameters**: `collect_config_examples=True`, `max_examples_per_config=10`
- Calls `extract_verb_config_examples()` after `tree.addspan()` and `get_dep_sizes()`
- Stores simplified tree dict (forms, upos, heads, deprels, verb_id, dep_ids)
- Limits collection to `max_examples_per_config` per configuration
- Returns examples in expanded tuple

#### `get_all_stats_parallel()`
Aggregates examples across all files:
- **New parameters**: `collect_config_examples=False`, `max_examples_per_config=10`
- Merges examples from multiple files per language
- Maintains limit of `max_examples_per_config` per configuration per language
- Returns `all_config_examples` dict (language → config → examples)

### HTML Generation (`generate_html_examples.py`)

Standalone module that generates HTML from saved examples (no CoNLL parsing):

**Main functions**:
- `load_config_examples()`: Load from `data/all_config_examples.pkl`
- `tree_dict_to_reactive_dep_tree_html()`: Convert tree dict to reactive-dep-tree format
- `generate_language_html()`: Create HTML files for each language
- `generate_index_html()`: Create organized index with 3-column layout
- `generate_all_html()`: Main entry point (can use parallel processing)

**Output structure**:
```
html_examples/
  index.html                     # Navigation page
  LanguageName_code/
    V_X.html                     # Individual configurations
    V_X_X.html
    X_V.html
    ...
```

### Data Extraction (`run_data_extraction.py`)

The main script enables example collection:
```python
collect_config_examples = True
max_examples_per_config = 10
```

Saves results to `data/all_config_examples.pkl` with structure:
```python
{
  'ab': {
    'V X X': [
      {'tree': {...}, 'verb_id': 1, 'dep_ids': [2, 3]},
      # ... up to 10 examples
    ]
  }
}
```

## Design Principles

### Guaranteed Consistency
Examples are collected **during** constituent size computation, not separately:
- Same loop iteration (after `tree.addspan()`, `get_dep_sizes()`)
- Identical dependency relation filters
- Same bastard inclusion logic
- No risk of constraint mismatch

### Minimal Storage
Only essential fields stored per example:
- `forms`: Word strings
- `upos`: POS tags
- `heads`: Head indices (1-based)
- `deprels`: Dependency relations
- `verb_id`, `dep_ids`: For highlighting

Full Sentence objects and unnecessary metadata excluded.

### Two-Phase Architecture
1. **Collection phase** (slow, run once): Integrated into main data extraction
2. **Generation phase** (fast, repeatable): Create HTML from saved examples

Benefits:
- HTML can be regenerated with different styling instantly
- No duplicate CoNLL file parsing required
- Examples always match current computation constraints

## Files Modified/Created

### Modified
1. **conll_processing.py**
   - Added `extract_verb_config_examples()` function
   - Modified `process_file_complete()` to collect examples
   - Modified `get_all_stats_parallel()` to aggregate examples

2. **run_data_extraction.py**
   - Added `collect_config_examples=True` flag
   - Added pickle save for examples

### Created
1. **generate_html_examples.py** - Generate HTML from saved examples
2. **test_config_integration.py** - Test example collection
3. **test_html_generation.py** - Test HTML generation

## Next Steps

1. **Run full extraction**: `python3 run_data_extraction.py`
2. **Generate HTML**: `python3 generate_html_examples.py`
3. **Browse examples**: Open `html_examples/index.html`
4. **Optional**: Regenerate HTML with custom styling (fast, no re-processing needed)

## Related Documentation

- [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md) - Overall module dependencies
- [HELIX_TABLE_METHODOLOGY.md](HELIX_TABLE_METHODOLOGY.md) - Dependency relation filters
