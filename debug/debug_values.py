
import os
import sys
import numpy as np
import conll_processing
from conll import conllFile2trees

TEST_FILE = 'data/bastard_examples/en_case_examples.conllu'

def main():
    print(f"Testing on {TEST_FILE}")
    if not os.path.exists(TEST_FILE):
        print("File not found.")
        return

    # 1. Run low-level accumulation
    position2sizes = {}
    position2num = {}
    sizes2freq = {}
    
    # Process trees manually
    trees = conllFile2trees(TEST_FILE)
    print(f"Loaded {len(trees)} trees.")
    
    for i, tree in enumerate(trees):
        tree.addspan(exclude=['punct'], compute_bastards=True)
        # Pass position2charsizes=None to ignore char logic for simplicity of test
        conll_processing.get_dep_sizes(tree, position2num, position2sizes, sizes2freq, include_bastards=True)
        
    print("\n--- Low-Level Accumulation ---")
    keys = list(position2sizes.keys())
    if not keys:
        print("No stats collected.")
        return
        
    sample_key = keys[0]
    print(f"Sample Key: {sample_key}")
    print(f"Num: {position2num[sample_key]}")
    print(f"Sum (Logs?): {position2sizes[sample_key]}")
    
    # Check if sum implies Log or Linear
    # If Linear, size >= 1. Sum >= Num.
    # If Log, size >= 1. Log >= 0. Sum >= 0.
    # If size=1, log=0.
    # If size=2, log=0.69.
    # If all sizes=1, Sum=0.
    # If Sum < Num (and many items), likely Logs.
    
    avg = position2sizes[sample_key] / position2num[sample_key]
    print(f"Arithmetic Mean of Accumulated Values: {avg}")
    
    # 2. Simulate conll_processing.get_type_freq_all_files_parallel logic
    print("\n--- Aggregation Logic ---")
    gm = np.exp(avg)
    print(f"Computed GM (exp(avg)): {gm}")
    
    
    # 3. Check what happens if we feed this to compute_average_sizes_table
    print("\n--- Downstream Logic ---")
    # compute_average_sizes_table takes Real Sizes (GM)
    # It does: np.log(GM) -> avg log -> exp
    
    inp_val = gm
    log_val = np.log(inp_val)
    print(f"Input to Downstream: {inp_val}")
    print(f"Log of Input: {log_val}")
    
    # If inp_val < 1 (impossible if generated from exp(avg >= 0)), log_val < 0.
    # If inp_val > 1, log_val > 0.
    
    print("\nDone.")

if __name__ == '__main__':
    main()
