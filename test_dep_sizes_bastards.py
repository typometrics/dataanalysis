
import sys
sys.path.append('/bigstorage/kim/typometrics/dataanalysis')
from conll import Tree
from conll_processing import get_dep_sizes

def test_dep_sizes_bastards():
    # Example: "he met a guy on Friday night who seemed really nice."
    # 2: met (VERB)
    # 4: guy (obj) -> 2
    # 9: seemed (acl:relcl) -> 4 (bastard of 2)
    
    # We want to verify that when include_bastards=True:
    # 1. 9 is included in the dependents of 2.
    # 2. The size of 9 is calculated using direct_span.
    # 3. The size of 4 is calculated using direct_span (excluding 9).
    
    t = Tree()
    t[1] = {'id': 1, 't': 'he', 'tag': 'PRON', 'gov': {2: 'nsubj'}}
    t[2] = {'id': 2, 't': 'met', 'tag': 'VERB', 'gov': {0: 'root'}}
    t[3] = {'id': 3, 't': 'a', 'tag': 'DET', 'gov': {4: 'det'}}
    t[4] = {'id': 4, 't': 'guy', 'tag': 'NOUN', 'gov': {2: 'obj'}}
    t[5] = {'id': 5, 't': 'on', 'tag': 'ADP', 'gov': {6: 'case'}}
    t[6] = {'id': 6, 't': 'Friday', 'tag': 'PROPN', 'gov': {2: 'obl'}}
    t[7] = {'id': 7, 't': 'night', 'tag': 'NOUN', 'gov': {6: 'flat'}}
    t[8] = {'id': 8, 't': 'who', 'tag': 'PRON', 'gov': {9: 'nsubj'}}
    t[9] = {'id': 9, 't': 'seemed', 'tag': 'VERB', 'gov': {4: 'acl:relcl'}}
    t[10] = {'id': 10, 't': 'really', 'tag': 'ADV', 'gov': {11: 'advmod'}}
    t[11] = {'id': 11, 't': 'nice', 'tag': 'ADJ', 'gov': {9: 'xcomp'}}
    
    t.addkids()
    
    # Run with bastards
    t.addspan(compute_bastards=True)
    
    print("Direct Span of 'guy' (4):", t[4].get('direct_span'))
    print("Bastards of 'met' (2):", t[2].get('bastards'))
    
    print("\nResults with include_bastards=True:")
    
    pos2num, pos2sizes, sizes2freq = {}, {}, {}
    get_dep_sizes(t, pos2num, pos2sizes, sizes2freq, include_bastards=True)

    # We expect 'met' (2) to have dependents:
    # Left: 1 (he)
    # Right: 4 (guy), 6 (Friday), 9 (seemed - bastard)
    # Total right kids: 3.
    
    key = 'average_totright_3'
    if key in sizes2freq:
        print(f"SUCCESS: Found key '{key}'.")
        # Expected sizes: [size(4), size(6), size(9)]
        # size(4) = 2 (direct)
        # size(6) = 3 (direct)
        # size(9) = 4 (direct)
        # kids_sizes = [2, 3, 4]
        dist = sizes2freq[key]
        print(f"Distribution: {dist}")
        
        if str([2, 3, 4]) in dist:
            print("SUCCESS: Found expected sizes [2, 3, 4].")
        else:
            print("FAILURE: Did not find expected sizes [2, 3, 4].")
    else:
        print(f"FAILURE: Did not find key '{key}'.")
            
    # Run WITHOUT bastards for comparison
    t.addspan(compute_bastards=False) # Reset spans
    
    pos2num, pos2sizes, sizes2freq = {}, {}, {}
    get_dep_sizes(t, pos2num, pos2sizes, sizes2freq, include_bastards=False)
    
    print("\nResults with include_bastards=False:")
    # We expect 'met' (2) to have dependents:
    # Left: 1
    # Right: 4, 6. (9 is part of 4)
    # Total right kids: 2.
    
    key = 'average_totright_2'
    if key in sizes2freq:
        print(f"SUCCESS: Found key '{key}'.")
        # Expected sizes: [size(4), size(6)]
        # size(4) = 6 (full span)
        # size(6) = 3 (full span)
        # kids_sizes = [6, 3]
        dist = sizes2freq[key]
        print(f"Distribution: {dist}")
        
        if str([6, 3]) in dist:
            print("SUCCESS: Found expected sizes [6, 3].")
        else:
            print("FAILURE: Did not find expected sizes [6, 3].")
    else:
        print(f"FAILURE: Did not find key '{key}'.")

    # Also check that 'seemed' (9) is processed
    # It has 1 left kid (8) and 1 right kid (11).
    # Key: average_totright_1
    # Size of 11 is 2.
    if 'average_totright_1' in sizes2freq:
        dist = sizes2freq['average_totright_1']
        # We might have multiple entries here if other verbs have 1 right kid.
        # But in this tree, only 'seemed' has 1 right kid?
        # 'met' has 3 (or 2).
        # So yes, only 'seemed'.
        if str([2]) in dist:
             print("SUCCESS: Found expected size [2] for 'seemed' right kid.")

    return t

if __name__ == "__main__":
    test_dep_sizes_bastards()
