
import pickle
import os
import sys

DATA_DIR = "data"
PICKLE_PATH = os.path.join(DATA_DIR, 'all_langs_average_sizes.pkl')
COUNT_PATH = os.path.join(DATA_DIR, 'all_langs_position2num.pkl')

def verify():
    if not os.path.exists(PICKLE_PATH):
        print(f"Error: {PICKLE_PATH} does not exist.")
        sys.exit(1)
        
    print(f"Loading {PICKLE_PATH}...")
    with open(PICKLE_PATH, 'rb') as f:
        data = pickle.load(f)
        
    print(f"Loaded data for {len(data)} languages.")
    
    # Check a few languages
    langs_to_check = list(data.keys())[:5]
    
    found_all_keys = False
    found_bilateral_keys = False
    
    for lang in langs_to_check:
        print(f"\nChecking language: {lang}")
        keys = data[lang].keys()
        
        # Check all_left/right
        has_all_left = 'all_left' in keys
        has_all_right = 'all_right' in keys
        print(f"  Has 'all_left': {has_all_left}")
        print(f"  Has 'all_right': {has_all_right}")
        
        if has_all_left and has_all_right:
            found_all_keys = True
            print(f"  all_left value: {data[lang]['all_left']}")
            print(f"  all_right value: {data[lang]['all_right']}")
            
        # Check bilateral keys
        bilateral_keys = [k for k in keys if k.startswith('bilateral_')]
        if bilateral_keys:
            found_bilateral_keys = True
            print(f"  Found {len(bilateral_keys)} bilateral keys.")
            print(f"  Example bilateral keys: {bilateral_keys[:3]}")
        else:
            print("  No bilateral keys found.")
            
    if found_all_keys and found_bilateral_keys:
        print("\nSUCCESS: Found both Global Mean keys and Bilateral keys.")
    else:
        print("\nFAILURE: Missing expected keys.")
        if not found_all_keys: print("- Missing all_left/all_right")
        if not found_bilateral_keys: print("- Missing bilateral keys")

    # Also check counts if available
    if os.path.exists(COUNT_PATH):
        print(f"\nLoading {COUNT_PATH}...")
        with open(COUNT_PATH, 'rb') as f:
            counts = pickle.load(f)
        
        lang = langs_to_check[0]
        if 'all_left' in counts[lang]:
             print(f"  Count for all_left in {lang}: {counts[lang]['all_left']}")
             
    
if __name__ == "__main__":
    verify()
