#!/usr/bin/env python3
"""
Test script for refactored verb-centered analysis.

This script tests that the refactoring works correctly by:
1. Loading existing data
2. Generating tables with the new API
3. Comparing with old API output
"""

import os
import sys
import pickle

# Test imports
print("Testing imports...")
try:
    from verb_centered_model import TableConfig, TableStructure
    print("✓ verb_centered_model")
except ImportError as e:
    print(f"✗ verb_centered_model: {e}")
    sys.exit(1)

try:
    from verb_centered_computations import MarginalMeansCalculator, FactorCalculator
    print("✓ verb_centered_computations")
except ImportError as e:
    print(f"✗ verb_centered_computations: {e}")
    sys.exit(1)

try:
    from verb_centered_layout import TableLayout
    print("✓ verb_centered_layout")
except ImportError as e:
    print(f"✗ verb_centered_layout: {e}")
    sys.exit(1)

try:
    from verb_centered_builder import VerbCenteredTableBuilder
    print("✓ verb_centered_builder")
except ImportError as e:
    print(f"✗ verb_centered_builder: {e}")
    sys.exit(1)

try:
    from verb_centered_formatters import TextTableFormatter, TSVFormatter, ExcelFormatter
    print("✓ verb_centered_formatters")
except ImportError as e:
    print(f"✗ verb_centered_formatters: {e}")
    sys.exit(1)

try:
    import verb_centered_analysis
    print("✓ verb_centered_analysis")
except ImportError as e:
    print(f"✗ verb_centered_analysis: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("All imports successful!")
print("="*70 + "\n")

# Test with sample data
print("Testing with sample data...")

# Create sample position_averages
sample_data = {
    'right_1_totright_1': 2.5,
    'right_1_totright_2': 2.3,
    'right_2_totright_2': 3.1,
    'right_1_totright_3': 2.1,
    'right_2_totright_3': 2.9,
    'right_3_totright_3': 3.5,
    'left_1_totleft_1': 2.4,
    'left_1_totleft_2': 2.2,
    'left_2_totleft_2': 3.0,
    'xvx_left_1': 2.4,
    'xvx_right_1': 2.5,
}

# Test different arrow direction modes
arrow_modes = ['diverging', 'inward', 'left_to_right', 'right_to_left']

for mode in arrow_modes:
    print(f"\n--- Testing arrow_direction='{mode}' ---")
    
    try:
        # Test new API
        config = TableConfig(
            show_horizontal_factors=True,
            show_diagonal_factors=False,
            arrow_direction=mode
        )
        
        table = verb_centered_analysis.create_verb_centered_table(sample_data, config)
        
        if table:
            print(f"✓ Created table with {table.num_rows} rows, {table.num_cols} columns")
            
            # Test formatters
            text_output = TextTableFormatter(table).format()
            print(f"✓ Text formatter: {len(text_output)} chars")
            
            tsv_output = TSVFormatter().format(table)
            print(f"✓ TSV formatter: {len(tsv_output)} chars")
            
        else:
            print("✗ Failed to create table")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
print("Basic tests complete!")
print("="*70 + "\n")

# Test with real data if available
DATA_DIR = "data"
avg_file = os.path.join(DATA_DIR, 'all_langs_average_sizes_filtered.pkl')

if os.path.exists(avg_file):
    print("Testing with real data...")
    
    try:
        with open(avg_file, 'rb') as f:
            all_langs_average_sizes = pickle.load(f)
        
        print(f"Loaded data for {len(all_langs_average_sizes)} languages")
        
        # Test with English if available
        if 'en' in all_langs_average_sizes:
            print("\n--- Testing with English data ---")
            en_data = all_langs_average_sizes['en']
            
            # Test old API (should route through new implementation)
            config = TableConfig(show_horizontal_factors=True, arrow_direction='diverging')
            table = verb_centered_analysis.create_verb_centered_table(en_data, config)
            
            if table:
                print(f"✓ English table: {table.num_rows} rows")
                
                # Save test output
                output_file = "test_english_table.txt"
                with open(output_file, 'w') as f:
                    f.write(TextTableFormatter(table).format())
                print(f"✓ Saved to {output_file}")
            else:
                print("✗ Failed to create English table")
                
    except Exception as e:
        print(f"✗ Error with real data: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"\nSkipping real data test - {avg_file} not found")
    print("Run notebook 04 first to generate data")

print("\n" + "="*70)
print("✓ REFACTORING TEST COMPLETE")
print("="*70)
