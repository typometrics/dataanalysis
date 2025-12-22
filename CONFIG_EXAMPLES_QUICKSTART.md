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
4. **CONFIG_EXAMPLES_INTEGRATION.md** - Technical documentation
5. **CONFIG_EXAMPLES_QUICKSTART.md** - This file

## Next Steps

1. **Run full extraction**: `python3 run_data_extraction.py`
2. **Generate HTML**: `python3 generate_html_examples.py`
3. **Browse examples**: Open `html_examples/index.html`
4. **Optional**: Update notebook to use collected examples
5. **Optional**: Regenerate HTML with custom styling

## Questions?

See detailed documentation in:
- **CONFIG_EXAMPLES_INTEGRATION.md** - Full technical details
- **conll_processing.py** - Source code with comments
- **generate_html_examples.py** - HTML generation code
