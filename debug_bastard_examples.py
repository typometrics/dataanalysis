
from conll import Tree
from conll_processing import get_bastard_stats

def test_bastard_examples():
    # Create a tree with a bastard
    # "he met a guy on Friday night who seemed really nice"
    # "who" (9) is a bastard of "met" (2)
    
    tree = Tree()
    tree[1] = {'t': 'he', 'tag': 'PRON', 'gov': {2: 'nsubj'}}
    tree[2] = {'t': 'met', 'tag': 'VERB', 'gov': {0: 'root'}}
    tree[3] = {'t': 'a', 'tag': 'DET', 'gov': {4: 'det'}}
    tree[4] = {'t': 'guy', 'tag': 'NOUN', 'gov': {2: 'obj'}}
    tree[5] = {'t': 'on', 'tag': 'ADP', 'gov': {6: 'case'}}
    tree[6] = {'t': 'Friday', 'tag': 'PROPN', 'gov': {2: 'obl'}}
    tree[7] = {'t': 'night', 'tag': 'NOUN', 'gov': {6: 'nmod'}}
    tree[8] = {'t': 'who', 'tag': 'PRON', 'gov': {9: 'nsubj'}}
    tree[9] = {'t': 'seemed', 'tag': 'VERB', 'gov': {4: 'acl:relcl'}}
    tree[10] = {'t': 'really', 'tag': 'ADV', 'gov': {11: 'advmod'}}
    tree[11] = {'t': 'nice', 'tag': 'ADJ', 'gov': {9: 'xcomp'}}
    tree[12] = {'t': '.', 'tag': 'PUNCT', 'gov': {2: 'punct'}}
    
    tree.addkids()
    tree.addspan(compute_bastards=True)
    
    print("Bastards of 2:", tree[2].get('bastards'))
    
    v, b, r, ex = get_bastard_stats(tree)
    
    print(f"Verbs: {v}")
    print(f"Bastards: {b}")
    print(f"Relations: {r}")
    print(f"Examples keys: {list(ex.keys())}")
    
    if 'acl' in ex:
        print("Example for 'acl' found.")
        print("Length of example:", len(ex['acl'][0]))
        print("First 50 chars:", ex['acl'][0][:50])
    else:
        print("ERROR: No example for 'acl' found.")

if __name__ == "__main__":
    test_bastard_examples()
