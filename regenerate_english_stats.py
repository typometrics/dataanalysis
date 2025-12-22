
import os
import pickle
import numpy as np
import data_utils
import conll_processing
import verb_centered_analysis
import sys

# Configuration
DATA_DIR = 'data'
TARGET_LANG = 'en'
METADATA_FILE = os.path.join(DATA_DIR, 'metadata.pkl')

def main():
    print(f"Loading metadata from {METADATA_FILE}...")
    if not os.path.exists(METADATA_FILE):
        print(f"Error: {METADATA_FILE} not found.")
        sys.exit(1)
        
    metadata = data_utils.load_metadata(METADATA_FILE)
    langShortConllFiles = metadata['langShortConllFiles']
    
    if TARGET_LANG not in langShortConllFiles:
        print(f"Error: Language '{TARGET_LANG}' not found in metadata.")
        sys.exit(1)
        
    files = langShortConllFiles[TARGET_LANG]
    print(f"Found {len(files)} files for '{TARGET_LANG}'. Processing...")
    
    # Process files using current logic (with np.exp fix)
    # Using small batch size or just passing list
    # get_type_freq_all_files_parallel takes a list of files
    
    # Need to check signature of get_type_freq_all_files_parallel
    # Arg 1: allshortconll (list of files)
    # Kwargs: include_bastards=True? compute_sentence_disorder=True?
    # Based on notebook, it calls with various args.
    # Default is include_bastards=True
    
    # Disorder logic is missing in current codebase, leading to NameError.
    # Disabling it to verify SIZE calculation.
    compute_sentence_disorder = False
    
    # Run processing
    # returns: all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, all_langs_average_charsizes, sentence_disorder_percentages
    # But since we pass ONLY English files, the result dictionaries will only contain 'en' keys if the function doesn't infer language from filename but from the loop.
    # Actually get_dep_sizes_file returns (lang, ...).
    # lang is parsed from filename.
    # So results will be keyed by 'en'.
    
    results = conll_processing.get_type_freq_all_files_parallel(
        files, 
        include_bastards=True, 
        compute_sentence_disorder=compute_sentence_disorder
    )
    
    if compute_sentence_disorder:
         _, _, all_langs_average_sizes, _, sentence_disorder_percentages = results
    else:
         _, _, all_langs_average_sizes, _ = results
         sentence_disorder_percentages = None

    print("Processing complete.")
    
    if TARGET_LANG not in all_langs_average_sizes:
        print(f"Error: No results for '{TARGET_LANG}' after processing.")
        sys.exit(1)
        
    # Stats for English
    en_averages = verb_centered_analysis.compute_average_sizes_table({TARGET_LANG: all_langs_average_sizes[TARGET_LANG]})
    
    # Formatting
    en_ordering_stats = None
    if sentence_disorder_percentages and TARGET_LANG in sentence_disorder_percentages:
        en_ordering_stats = sentence_disorder_percentages[TARGET_LANG]

    table_str = verb_centered_analysis.format_verb_centered_table(
        en_averages,
        show_horizontal_factors=True,
        show_diagonal_factors=True,
        show_ordering_triples=True,
        show_row_averages=True,
        ordering_stats=en_ordering_stats,
        arrow_direction='diverging' # or rightwards?
    )
    
    print("\n--- REGENERATED TABLE FOR ENGLISH ---")
    print(table_str)

if __name__ == '__main__':
    main()
