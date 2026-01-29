
import pickle
import os
import sys

# Add path
sys.path.append('/bigstorage/kim/typometrics/dataanalysis')
from verb_centered_analysis import compute_sizes_table, create_verb_centered_table
from verb_centered_formatters import TextTableFormatter

DATA_DIR = "data"
PICKLE_PATH = os.path.join(DATA_DIR, 'all_langs_average_sizes.pkl')

def verify_table():
    print(f"Loading {PICKLE_PATH}...")
    with open(PICKLE_PATH, 'rb') as f:
        data = pickle.load(f)
        
    lang = 'abq'
    if lang not in data:
        lang = list(data.keys())[0]
        
    print(f"Generating table for language: {lang}")
    lang_data = data[lang]
    
    # Store expected values
    expected_l = lang_data.get('all_left')
    expected_r = lang_data.get('all_right')
    print(f"Expected Mean(X*) Left: {expected_l}")
    print(f"Expected Mean(X*) Right: {expected_r}")
    
    # Compute table data
    results, validation = compute_sizes_table({lang: lang_data}, table_type='standard')
    
    # Check if results contain 'all_left'
    if 'all_left' in results:
        print(f"compute_sizes_table output 'all_left': {results['all_left']}")
    else:
        print("FAILURE: compute_sizes_table did not return 'all_left'")
        
    if 'factor_all_right_vs_all_left' in results:
         print(f"compute_sizes_table output 'factor_all_right_vs_all_left': {results['factor_all_right_vs_all_left']}")
    
    # Generate Table Structure
    table = create_verb_centered_table(
        results,
        show_horizontal_factors=True,
        show_row_averages=True
    )
    
    # Format Text
    formatter = TextTableFormatter(table)
    text_output = formatter.format()
    
    print("\n--- Generated Table (Fragment) ---")
    # visual inspection of central row
    lines = text_output.split('\n')
    found_central = False
    for line in lines:
        if "Mean(X*)" in line:
            print(line)
            found_central = True
            
    if found_central:
        print("\nSUCCESS: Found central row 'Mean(X*) V Mean(X*)'")
    else:
        print("\nFAILURE: Did not find central row label")

if __name__ == "__main__":
    verify_table()
