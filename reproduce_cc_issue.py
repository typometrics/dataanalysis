
import sys
import os

# Add local directory to path so we can import modules
sys.path.append(os.getcwd())

from conll import Tree
from conll_processing import get_dep_sizes, get_ordering_stats

def test_cc_exclusion():
    print("Testing 'cc' exclusion in configuration search...")
    
    # Create a mock tree
    # 1: "and", cc, head=2
    # 2: "gone", root, VERB
    # 3: "home", obj, head=2
    
    tree = Tree()
    tree[1] = {'id': 1, 't': 'and', 'tag': 'CCONJ', 'gov': {2: 'cc'}, 'span': [1]}
    tree[2] = {'id': 2, 't': 'gone', 'tag': 'VERB', 'gov': {0: 'root'}, 'span': [1, 2, 3]}
    tree[3] = {'id': 3, 't': 'home', 'tag': 'NOUN', 'gov': {2: 'obj'}, 'span': [3]}
    
    # Manually add 'kids' which is usually done by tree.addkids()
    # But get_dep_sizes expects 'kids' to be populated.
    # conll.py's addkids does: self[g]["kids"][i]=f 
    tree.addkids()
    
    # Check tree structure
    print(f"Tree structure: {tree.conllu()}")
    print(f"Kids of V (node 2): {tree[2]['kids']}")
    
    # 1. Test get_dep_sizes
    position2num, position2sizes, sizes2freq = {}, {}, {}
    get_dep_sizes(tree, position2num, position2sizes, sizes2freq)
    
    print("\nResults from get_dep_sizes:")
    print("position2num keys:", position2num.keys())
    
    # Expect: 'right_1' (for object), maybe 'right_1_totright_1'. 
    # But 'left_1' (for cc) should be MISSING if excluded.
    
    has_left = any(k.startswith('left') for k in position2num)
    has_right = any(k.startswith('right') for k in position2num)
    
    print(f"Has Left configuration (should be False): {has_left}")
    print(f"Has Right configuration (should be True): {has_right}")
    
    if has_left:
        print("FAIL: 'cc' dependent was included in Left configuration!")
    else:
        print("SUCCESS: 'cc' dependent was cleanly excluded from Left configuration.")
        
    # 2. Test get_ordering_stats
    stats = get_ordering_stats(tree)
    print("\nResults from get_ordering_stats:")
    print(stats)
    
    # Expect 'right' keys, but NO 'left' keys.
    has_left_stats = any(k[0] == 'left' for k in stats)
    print(f"Has Left ordering stats (should be False): {has_left_stats}")

    if has_left_stats:
        print("FAIL: 'cc' dependent was included in ordering stats!")
    else:
        print("SUCCESS: 'cc' dependent was cleanly excluded from ordering stats.")

if __name__ == "__main__":
    test_cc_exclusion()
