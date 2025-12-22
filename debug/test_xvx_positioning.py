#!/usr/bin/env python3
"""
Test the new X V X row positioning and reversed left-side ordering.
"""

import pickle
import verb_centered_analysis
from importlib import reload

# Load English data
print("Loading English data...")
with open('data/all_langs_average_sizes_filtered.pkl', 'rb') as f:
    data = pickle.load(f)

en_data = data.get('en', {})

print("\n" + "="*70)
print("Testing X V X Row Positioning and Left-Side Ordering")
print("="*70)

for direction in ['left_to_right', 'right_to_left', 'diverging', 'inward']:
    print(f"\n--- Arrow Direction: {direction} ---\n")
    
    reload(verb_centered_analysis)
    table = verb_centered_analysis.format_verb_centered_table(
        en_data,
        show_horizontal_factors=True,
        show_diagonal_factors=False,
        arrow_direction=direction
    )
    
    # Extract just the data rows (skip header and separators)
    lines = table.split('\n')
    data_lines = [l for l in lines if l.strip() and not l.startswith('---') and not l.startswith('Row')]
    
    # Find key rows
    for i, line in enumerate(data_lines):
        if 'R tot=4' in line:
            print(f"Row {i+1}: R tot=4 (top of right side)")
        elif 'R tot=1' in line:
            print(f"Row {i+1}: R tot=1 (bottom of right side)")
        elif 'X V X' in line:
            print(f"Row {i+1}: X V X *** MIDDLE ROW ***")
            # Show the actual XVX values
            if i < len(data_lines):
                print(f"    Content: {line[:80]}...")
        elif 'L tot=1' in line:
            print(f"Row {i+1}: L tot=1 (top of left side)")
        elif 'L tot=4' in line:
            print(f"Row {i+1}: L tot=4 (bottom of left side)")
        elif 'M Vert Left' in line:
            print(f"Row {i+1}: M Vert Left (marginal means)")

print("\n" + "="*70)
print("✓ Test complete!")
print("="*70)
