# Migration Summary: Configuration Example Generation

## Changes Made

### ✅ Removed Old Approach
1. **Deleted**: `conll_html_examples.py`
   - Old module that re-parsed CoNLL files separately
   - Used different scanning logic (might not match size computation constraints)
   - Required full CoNLL processing run just for examples

2. **Updated**: [04_data_processing.ipynb](04_data_processing.ipynb) Cell 15
   - Removed old code calling `conll_html_examples.generate_all_examples()`
   - Removed references to `data/configuration_examples/` output directory

### ✅ Added New Integrated Approach
1. **Updated**: [04_data_processing.ipynb](04_data_processing.ipynb) Cells 15-16
   - Cell 15 (markdown): New section header explaining the integrated approach
   - Cell 16 (code): New code using `generate_html_examples.py`
   - Checks for `data/all_config_examples.pkl` (collected during data extraction)
   - Generates HTML to `html_examples/` directory

## New Workflow

### Step 1: Data Extraction (Run Once)
```bash
python3 run_data_extraction.py
```
- Processes all CoNLL files
- Computes all metrics (sizes, VO/HI, disorder, etc.)
- **Collects configuration examples automatically**
- Saves to `data/all_config_examples.pkl`

### Step 2: Run Notebook 04
Open and run [04_data_processing.ipynb](04_data_processing.ipynb):
- Cell 15-16 will generate HTML from saved examples
- Fast: ~2-3 seconds (no CoNLL parsing)
- Output: `html_examples/index.html`

## Key Benefits

### ✅ Guaranteed Consistency
- Examples use **identical** constraints as constituent size computation
- Same dependency relations filter
- Same bastard inclusion logic
- Collected in the **same loop** as `get_dep_sizes()`

### ✅ No Duplicate Work
- Examples collected once during main data extraction
- No need to re-parse CoNLL files
- Faster overall workflow

### ✅ Better Organization
- Output in `html_examples/` instead of `data/configuration_examples/`
- Cleaner separation: data extraction → HTML generation
- Can regenerate HTML anytime without re-extracting

## File Changes Summary

### Deleted
- `conll_html_examples.py` (old approach)

### Modified
- [04_data_processing.ipynb](04_data_processing.ipynb) - Cell 15-16 updated

### Existing (Created Earlier)
- [generate_html_examples.py](generate_html_examples.py) - New HTML generator
- [conll_processing.py](conll_processing.py) - Integrated example collection
- [run_data_extraction.py](run_data_extraction.py) - Saves examples
- [CONFIG_EXAMPLES_QUICKSTART.md](CONFIG_EXAMPLES_QUICKSTART.md) - User guide
- [CONFIG_EXAMPLES_INTEGRATION.md](CONFIG_EXAMPLES_INTEGRATION.md) - Technical docs

## Testing

Run the test to verify everything works:
```bash
python3 test_config_integration.py
python3 test_html_generation.py
```

Both should pass with ✅

## Rollback (If Needed)

If you need to revert to the old approach:
1. Restore `conll_html_examples.py` from git: `git checkout conll_html_examples.py`
2. Revert notebook cell 15-16 changes
3. Set `collect_config_examples=False` in `run_data_extraction.py`

## Next Steps

1. **Run data extraction** (if not already done):
   ```bash
   python3 run_data_extraction.py
   ```

2. **Run notebook 04** to generate HTML:
   - Open [04_data_processing.ipynb](04_data_processing.ipynb)
   - Run cells 1-16
   - Open `html_examples/index.html`

3. **Verify output**:
   - Check that examples match constituent size computations
   - Verify bastard dependents are included correctly
   - Compare with old approach if needed

## Questions?

See:
- [CONFIG_EXAMPLES_QUICKSTART.md](CONFIG_EXAMPLES_QUICKSTART.md) - Quick start guide
- [CONFIG_EXAMPLES_INTEGRATION.md](CONFIG_EXAMPLES_INTEGRATION.md) - Technical details
