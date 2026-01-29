import sys
import os

# Add the directory to path
sys.path.append('/bigstorage/kim/typometrics/dataanalysis')

# Mock data needed for compute_averaged_ordering_stats
from verb_centered_analysis import compute_averaged_ordering_stats

print("Testing compute_averaged_ordering_stats with mixed types...")

# Mock ordering stats with mixed dictionary and integer values
mock_ordering_stats = {
    'lang1': {
        'key1': {'lt': 10, 'eq': 5, 'gt': 5}, # Valid dict
        'total_count': 100, # Invalid int
        'key2': {'lt': 20, 'eq': 0, 'gt': 0}  # Valid dict
    },
    'lang2': {
        'key1': {'lt': 5, 'eq': 5, 'gt': 10},
        'total_count': 200
    }
}

try:
    aggregated = compute_averaged_ordering_stats(['lang1', 'lang2'], mock_ordering_stats)
    print("SUCCESS: compute_averaged_ordering_stats ran without AttributeError")
    
    # Check results
    if 'key1' in aggregated:
        print(f"Aggregated key1: {aggregated['key1']}")
    else:
        print("FAILURE: key1 missing from aggregated results")
        
    if 'total_count' in aggregated:
        print("FAILURE: total_count (int) erroneously included in results")
    else:
        print("SUCCESS: total_count correctly excluded")
        
except Exception as e:
    print(f"FAILURE: Exception raised: {e}")
    sys.exit(1)

# ... rest of verification ...
from verb_centered_builder import VerbCenteredTableBuilder, TableConfig
from verb_centered_formatters import TextTableFormatter

# Mock data
position_averages = {
    'right_1_totright_2': 1.5,
    'right_2_totright_2': 1.2,
    'all_left': 2.5,
    'all_right': 3.0
}
config = TableConfig(
    show_horizontal_factors=True,
    show_diagonal_factors=True,
    show_ordering_triples=True,
    show_row_averages=True, 
    show_marginal_means=True,
    arrow_direction='outward'
)
builder = VerbCenteredTableBuilder(position_averages, config, None)
table = builder.build()
formatter = TextTableFormatter(table)
print(formatter.format())
