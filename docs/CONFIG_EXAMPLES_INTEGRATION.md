# Configuration Example Collection Integration

## Overview

The configuration example collection has been fully integrated into the main data processing pipeline. Examples are now collected during the same loop as constituent size computation, ensuring consistent constraints and avoiding duplicate file parsing.

## Implementation

### 1. Core Processing (`conll_processing.py`)

#### New Function: `extract_verb_config_examples()`
- **Location**: Lines ~1070-1093
- **Purpose**: Extract configuration string from verb tree (mirrors `get_dep_sizes()` logic)
- **Logic**: Uses same dependency relation filters and bastard inclusion as size computation
- **Output**: Configuration string (e.g., "V X X" or "X X X V")

#### Modified: `process_file_complete()`
- **New Parameters**:
  - `collect_config_examples=True`: Enable example collection
  - `max_examples_per_config=10`: Limit per configuration
  
- **Changes**:
  - Added `config_examples` container initialization
  - In processing loop (after `tree.addspan()` and `get_dep_sizes()`):
    - Calls `extract_verb_config_examples()` to get configuration
    - Stores tree dict with verb_id and dep_ids
    - Limits to `max_examples_per_config` per configuration
  - Return tuple expanded to 11 elements (added `config_examples` as last element)

#### Modified: `get_all_stats_parallel()`
- **New Parameters**:
  - `collect_config_examples=False`: Control collection
  - `max_examples_per_config=10`: Example limit
  
- **Changes**:
  - Added `all_config_examples` aggregator dict
  - Updated `functools.partial` to pass new parameters
  - Added aggregation logic for config examples (section 5)
  - Aggregates up to `max_examples_per_config` per language per configuration
  - Return tuple conditionally includes `all_config_examples`

### 2. Data Extraction Script (`run_data_extraction.py`)

**Changes**:
- Set `collect_config_examples=True` by default
- Updated result unpacking to handle optional `all_config_examples`
- Save examples to `data/all_config_examples.pkl`

**Output Format**:
```python
all_config_examples = {
    'ab': {  # Language code
        'V X X': [  # Configuration
            {
                'tree': {
                    'forms': ['word1', 'word2', ...],
                    'upos': ['VERB', 'NOUN', ...],
                    'heads': [0, 1, ...],
                    'deprels': ['root', 'obj', ...]
                },
                'verb_id': 1,  # 1-based index
                'dep_ids': [2, 3]  # 1-based indices
            },
            # ... up to 10 examples
        ],
        'X X V': [...],
        # ... more configurations
    },
    'en': {...},
    # ... more languages
}
```

### 3. HTML Generation (`generate_html_examples.py`)

**New Module** - Generates HTML from saved examples (no CoNLL parsing):

**Functions**:
- `load_config_examples()`: Load pickled examples
- `load_metadata()`: Load language names
- `tree_dict_to_reactive_dep_tree_html()`: Convert tree dict to HTML
- `generate_language_html()`: Create HTML files per language
- `generate_index_html()`: Create organized index with 3-column layout
- `generate_all_html()`: Main entry point with parallel processing

**Usage**:
```python
from generate_html_examples import generate_all_html
generate_all_html(data_dir='data', output_dir='html_examples')
```

## Workflow

### Step 1: Data Extraction (Collect Examples)
```bash
python run_data_extraction.py
```

This processes all CoNLL files and:
1. Computes constituent sizes (existing)
2. Computes VO/HI scores (existing)
3. Computes sentence disorder (existing)
4. **Collects configuration examples** (NEW)
5. Saves to `data/all_config_examples.pkl`

### Step 2: HTML Generation (From Saved Examples)
```bash
python generate_html_examples.py
```

This generates HTML files:
1. Loads `data/all_config_examples.pkl`
2. Loads language names from `data/metadata.pkl`
3. Generates HTML files per configuration per language
4. Creates `html_examples/index.html` with navigation

**Output Structure**:
```
html_examples/
  index.html
  Abkhaz_ab/
    V_X_X.html
    V_X_X_X.html
    X_X_V.html
    ...
  English_en/
    V_X_X.html
    ...
```

## Key Design Decisions

### 1. Same Constraints as Size Computation
Configuration examples use **identical** constraints:
- Only VERB governors (same as size computation)
- Same dependency relations: nsubj, obj, iobj, csubj, ccomp, xcomp, obl, expl, dislocated, advcl, advmod, nmod, appos, nummod, acl, amod
- Respects `include_bastards` flag consistently
- Collected in **same loop** after `tree.addspan()` and `get_dep_sizes()`

### 2. Minimal Tree Storage
Only stores what's needed for HTML generation:
- `forms`: Word forms
- `upos`: POS tags
- `heads`: Head indices
- `deprels`: Dependency relations
- `verb_id`: Verb position for highlighting
- `dep_ids`: Dependent positions for highlighting

Avoids storing full Sentence objects or unnecessary fields.

### 3. Two-Phase Architecture
1. **Data extraction phase**: Collect examples once during main processing
2. **HTML generation phase**: Generate HTML from saved examples (fast, repeatable)

Benefits:
- No duplicate CoNLL parsing
- HTML can be regenerated with different styling without re-processing
- Examples collected with guaranteed constraint consistency

### 4. Efficient Aggregation
- Uses `max_examples_per_config` to limit memory
- First-come-first-served example selection
- Aggregates across multiple files per language
- Parallel processing for both collection and HTML generation

## Testing

To test the integration:

```bash
# 1. Run data extraction (includes example collection)
python run_data_extraction.py

# 2. Verify examples were saved
python -c "import pickle; d = pickle.load(open('data/all_config_examples.pkl', 'rb')); print(f'{len(d)} languages, {sum(len(c) for c in d.values())} total configs')"

# 3. Generate HTML
python generate_html_examples.py

# 4. Check output
ls html_examples/
```

## Performance

With 80 CPU cores and ~185 languages:
- **Data extraction**: ~10-15 minutes (includes all metrics + examples)
- **HTML generation**: ~2-3 seconds (from saved examples)
- **Total**: Similar to original processing time (minimal overhead)

## Migration from Old Approach

### Old: `conll_html_examples.py`
- Parsed CoNLL files separately
- Different constraints (might not match size computation)
- Required full CoNLL re-processing for examples

### New: Integrated approach
- Examples collected during main processing
- Guaranteed same constraints
- No duplicate parsing
- Faster overall workflow

## Future Enhancements

Possible improvements:
1. Add sentence text metadata for easier verification
2. Support filtering examples by sentence length
3. Add configuration statistics to index page
4. Generate comparison views between languages
5. Add interactive filtering in HTML

## Files Modified

1. **conll_processing.py**:
   - Added `extract_verb_config_examples()` function
   - Modified `process_file_complete()` signature and logic
   - Modified `get_all_stats_parallel()` to aggregate examples

2. **run_data_extraction.py**:
   - Added `collect_config_examples=True`
   - Updated result unpacking
   - Added pickle save for examples

3. **generate_html_examples.py** (NEW):
   - Full HTML generation from saved examples
   - Parallel processing
   - Organized index with 3-column layout

## Summary

Configuration examples are now collected as an **integrated part** of the main data processing pipeline, ensuring:
- ✅ Same constraints as constituent size computation
- ✅ Bastard dependents included consistently
- ✅ No duplicate CoNLL file parsing
- ✅ Efficient memory usage with example limits
- ✅ Fast HTML regeneration from saved examples
- ✅ Organized output matching table naming conventions
