# Sentence-Level Disorder Analysis

## Overview

The disorder analysis now supports two approaches:

1. **Average-level disorder** (original): Checks if the average constituent sizes are ordered
   - Result: Binary flag per language (ordered or disordered)
   - Fast computation (already computed from averaged data)

2. **Sentence-level disorder** (new): Checks what percentage of individual sentences have disordered constituents
   - Result: Percentage per language (0-100%)
   - Slower computation (requires parsing all individual sentences)

## Architecture

### Where is it computed?

**Notebook 02 (`02_dependency_analysis.ipynb`)** - Section 2b

The sentence-level disorder computation is now integrated into the main parallel processing pipeline in notebook 02, alongside the existing constituent size analysis.

**Benefits of this approach:**
- All CoNLL file parsing happens in one place
- Efficient: trees are parsed only once for both analyses
- Leverages existing parallel processing infrastructure
- Data is ready for downstream analyses in notebook 04

### Code Structure

**`conll_processing.py`** contains three new/modified functions:

1. `get_sentence_disorder(tree, include_bastards=False)`: 
   - Analyzes a single sentence tree
   - Returns disorder flags for each verb's configuration
   - Uses the same verb/dependency filtering as existing code

2. `get_dep_sizes_file(..., compute_sentence_disorder=False)`:
   - Modified to optionally compute sentence disorder
   - Returns additional sentence_disorder_stats when enabled

3. `get_type_freq_all_files_parallel(..., compute_sentence_disorder=False)`:
   - Modified to optionally compute sentence disorder in parallel
   - Returns additional sentence_disorder_percentages when enabled
   - Aggregates results across all files per language

## Usage

### Step 1: Generate sentence-level disorder data

Open `02_dependency_analysis.ipynb` and find section 2b:

```python
# Set to True to enable sentence-level disorder computation
compute_sentence_disorder = True
```

Run the notebook. This will:
- Take 10-30 minutes (processes all sentences in all CoNLL files)
- Generate `data/sentence_disorder_percentages.csv`
- Generate `data/sentence_disorder_percentages.pkl`

### Step 2: Analyze results

Open `04_data_processing.ipynb` and run section 7c.

This will:
- Load the pre-computed sentence disorder data
- Compare sentence-level vs average-level disorder
- Show which languages have the largest differences between the two approaches

## Data Format

### sentence_disorder_percentages.csv

Columns:
- `language_code`: ISO language code (e.g., 'en')
- `language_name`: Full language name (e.g., 'English')
- `group`: Language family/group
- `right_tot_2_pct`: % of "V X X" sentences that are disordered
- `right_tot_2_total`: Total number of "V X X" sentences analyzed
- `right_tot_2_disordered`: Number of disordered "V X X" sentences
- Similar columns for `right_tot_3`, `right_tot_4`, `left_tot_2`, `left_tot_3`, `left_tot_4`

## Key Differences Between Approaches

### Example: Right tot=2 (V X X)

**Average-level approach:**
- Compute avg(pos1) and avg(pos2) across all sentences
- Check if avg(pos1) < avg(pos2)
- Result: Binary (6.5% of languages have disordered averages)

**Sentence-level approach:**
- For each sentence, check if actual pos1 < actual pos2
- Count how many sentences are disordered
- Result: Percentage (e.g., 15% of sentences are disordered on average across languages)

### Why do they differ?

A language can have **ordered averages** but still have **many disordered sentences** if:
- Most sentences follow the pattern, but outliers exist
- Variability is high: some sentences have very small pos1, others have very large pos1
- The average "smooths out" the disorder present in individual sentences

Conversely, a language can have **disordered averages** but **few disordered sentences** if:
- The averages are close (e.g., avg(pos1) = 2.01, avg(pos2) = 1.99)
- Most sentences are actually ordered, but the averages swap due to aggregation

## Performance Notes

- **Without sentence disorder**: ~1-2 minutes on typical hardware
- **With sentence disorder**: ~10-30 minutes on typical hardware
- Uses all available CPU cores via multiprocessing
- Memory usage is modest (processes files in chunks)

## Troubleshooting

### "Sentence disorder data not found"

**Solution**: Run notebook 02 with `compute_sentence_disorder=True`

### "AttributeError: 'int' object has no attribute 'get'"

**Solution**: This was a bug in the old `compute_sentence_disorder.py` module. The new implementation is integrated into `conll_processing.py` and uses the correct tree structure.

### Computation is too slow

**Options**:
1. Disable sentence disorder computation (set to `False`)
2. Use a smaller dataset (test on a subset of languages)
3. The computation is already parallelized - you're getting maximum speed

## File Changes

### Modified files:
- `conll_processing.py`: Added sentence disorder functions
- `02_dependency_analysis.ipynb`: Added section 2b for optional sentence disorder computation
- `04_data_processing.ipynb`: Section 7c now loads pre-computed data

### Deprecated files:
- `compute_sentence_disorder.py`: No longer used (integrated into conll_processing.py)

### New output files:
- `data/sentence_disorder_percentages.csv`
- `data/sentence_disorder_percentages.pkl`
