
import os
import sys
import numpy as np

# Mocking the necessary classes/functions from conll_processing
# distinct from the actual file to ensure isolation, but using the exact logic logic I want to test
# Actually, better to import the actual file to test the ACTUAL code.

sys.path.append(os.getcwd())
try:
    from conll_processing import get_dep_sizes, process_kids
except ImportError:
    print("Could not import conll_processing. Make sure you are in the right directory.")
    sys.exit(1)

# Mock a Tree object
class MockTree(dict):
    def __init__(self):
        super().__init__()
    def addspan(self, exclude=None, compute_bastards=False):
        pass # We will manually set spans

def create_mock_tree():
    # Structure: 1(X3) 2(X2) 3(X1) 4(V)
    # Sizes: X3=10, X2=5, X1=1
    tree = MockTree()
    
    # Spans (Values must be in tree)
    span1 = [1] + list(range(101, 110)) # Size 10
    span2 = [2] + list(range(201, 205)) # Size 5
    span3 = [3]                         # Size 1
    span4 = [1, 2, 3, 4]                # Size 4 (V + Kids)
    
    # Node 1: X3 (Leftmost)
    tree[1] = {'tag': 'NOUN', 'span': span1, 'kids': {}, 'gov': {4: 'obj'}, 't': 'X3', 'direct_span': span1}
    # Node 2: X2
    tree[2] = {'tag': 'NOUN', 'span': span2, 'kids': {}, 'gov': {4: 'obj'}, 't': 'X2', 'direct_span': span2}
    # Node 3: X1 (Closest to V)
    tree[3] = {'tag': 'NOUN', 'span': span3, 'kids': {}, 'gov': {4: 'obj'}, 't': 'X1', 'direct_span': span3}
    
    # Node 4: V (Head)
    tree[4] = {
        'tag': 'VERB', 
        'span': span4,
        'kids': {1: 'obj', 2: 'obj', 3: 'obj'}, 
        'gov': {0: 'root'},
        't': 'V'
    }
    
    # Fill missing nodes
    all_spans = span1 + span2 + span3 + span4
    for nid in all_spans:
        if nid not in tree:
            tree[nid] = {'t': 'x', 'tag': 'X', 'span': [nid]}
            
    return tree

def test_extraction():
    tree = create_mock_tree()
    
    position2num = {}
    position2sizes = {}
    sizes2freq = {}
    position2charsizes = {}
    
    # Mocking deps list
    # In conll_processing, deps is usually set globally or passed. 
    # But get_dep_sizes hardcodes allow lists or uses defaults.
    # Actually get_dep_sizes uses global 'deps' variable in conll_processing. 
    # We might need to monkeypatch it if it's not available.
    import conll_processing
    conll_processing.deps = {'obj', 'nsubj', 'obl'} # Ensure relations are valid
    conll_processing.head_pos = {'VERB'}
    
    print("--- Running get_dep_sizes ---")
    get_dep_sizes(tree, position2num, position2sizes, sizes2freq, include_bastards=False, position2charsizes=position2charsizes)
    
    print("\n--- Extracted Global Stats (position2sizes) ---")
    # Values are sums of logs. Converting to GM.
    extracted_gms = {}
    for k, v in position2sizes.items():
        count = position2num[k]
        gm = np.exp(v / count)
        extracted_gms[k] = gm
        print(f"Key: {k}, Count: {count}, LogSum: {v:.4f}, GM: {gm:.4f}")

    return extracted_gms

def test_html_logic(global_stats):
    print("\n--- Simulating HTML Logic ---")
    
    # Setup Example Data matching the tree
    # Indices in HTML logic (calculate_position_stats):
    # Left deps: sorted indices. Node 1, 2, 3.
    # Ex: {1: size10, 2: size5, 3: size1} (IDs)
    # sorted(left_deps) -> [1, 2, 3].
    # Enumerate: 
    # i=0 -> d=1 (X3) -> Size 10
    # i=1 -> d=2 (X2) -> Size 5
    # i=2 -> d=3 (X1) -> Size 1
    
    left_sizes = {
        0: [10], # X3
        1: [5],  # X2
        2: [1]   # X1
    }
    
    l_count = 3
    r_count = 0
    
    indices = sorted(left_sizes.keys()) # [0, 1, 2]
    
    for i in indices:
        vals = left_sizes[i]
        local_gm = np.exp(np.mean(np.log(vals)))
        
        # HTML Logic
        dist = l_count - i
        # i=0 -> dist=3
        # i=1 -> dist=2
        # i=2 -> dist=1
        
        # Lookup Key
        # Trying specific key first (Total Length)
        tot_key = f"left_{dist}_totleft_{l_count}"
        if tot_key not in global_stats:
            # Fallback
            key = f"left_{dist}"
        else:
            key = tot_key
            
        global_val = global_stats.get(key, None)
        
        print(f"HTML Position i={i} (Node {i+1}). Calculated Dist={dist} (X{dist}).")
        print(f"  -> Local GM: {local_gm}")
        print(f"  -> Looking up Global Key: '{key}'")
        print(f"  -> Found Global Value: {global_val}")
        
        if abs(local_gm - global_val) < 0.001:
            print("  -> MATCH")
        else:
            print("  -> MISMATCH")

if __name__ == "__main__":
    gms = test_extraction()
    test_html_logic(gms)
